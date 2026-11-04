"""Android-first local video rendering through FFmpeg MediaCodec.

Designed for Termux on Android. Hardware MediaCodec support is detected at
runtime; no NVIDIA driver or nvidia-smi dependency is assumed. Software
encoding is opt-in and never silently selected.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from src.production_execution import AdapterResult
from src.production_job import ProductionJob


class AndroidVideoAdapterError(RuntimeError):
    """Raised when Android-local video prerequisites or outputs are invalid."""


@dataclass(frozen=True)
class AndroidVideoConfig:
    input_path: str
    output_root: str
    width: int = 1280
    height: int = 720
    fps: int = 30
    bitrate: str = "6M"
    allow_software_fallback: bool = False
    timeout_seconds: int = 1800

    def __post_init__(self) -> None:
        if not self.input_path or not self.output_root:
            raise ValueError("input_path and output_root are required")
        if self.width < 2 or self.height < 2 or self.width % 2 or self.height % 2:
            raise ValueError("width and height must be positive even integers")
        if not 1 <= self.fps <= 60:
            raise ValueError("fps must be between 1 and 60")
        if not isinstance(self.bitrate, str) or not self.bitrate.strip():
            raise ValueError("bitrate must be a non-empty FFmpeg bitrate value")
        if not isinstance(self.allow_software_fallback, bool):
            raise ValueError("allow_software_fallback must be boolean")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


class AndroidMediaCodecVideoAdapter:
    """Render one local video using Android MediaCodec, with explicit CPU opt-in."""

    name = "android-ffmpeg-mediacodec"

    def __init__(
        self,
        config: AndroidVideoConfig,
        *,
        runner: Callable = subprocess.run,
        clock: Callable = time.monotonic,
    ) -> None:
        self.config = config
        self.runner = runner
        self.clock = clock

    def execute(self, job: ProductionJob) -> AdapterResult:
        if not isinstance(job, ProductionJob):
            raise TypeError("job must be a ProductionJob")
        if job.asset_type != "video":
            return AdapterResult(False, error_message="Android video adapter only supports video jobs")
        if job.status != "running":
            return AdapterResult(False, error_message="job must be in running status")

        started = datetime.now(timezone.utc)
        start_clock = self.clock()
        output_root = Path(self.config.output_root).resolve()
        source = Path(self.config.input_path).resolve()
        output_path = output_root / f"{job.job_id}-{uuid4().hex}.mp4"
        manifest_path = output_root / f"{job.job_id}-{output_path.stem.rsplit('-', 1)[-1]}.execution.json"

        try:
            if not source.is_file() or source.stat().st_size <= 0:
                raise AndroidVideoAdapterError("input video must be an existing non-empty file")
            if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
                raise AndroidVideoAdapterError("ffmpeg and ffprobe must both be installed (Termux: pkg install ffmpeg)")
            output_root.mkdir(parents=True, exist_ok=True)

            ffmpeg_version = self._run(
                ["ffmpeg", "-version"], timeout=15, capture_output=True, text=True, check=False
            )
            if ffmpeg_version.returncode != 0:
                raise AndroidVideoAdapterError("could not read FFmpeg version")
            encoder_list = self._run(
                ["ffmpeg", "-hide_banner", "-encoders"], timeout=30,
                capture_output=True, text=True, check=False,
            )
            if encoder_list.returncode != 0:
                raise AndroidVideoAdapterError("could not inspect FFmpeg encoders")
            available = encoder_list.stdout or ""
            if "h264_mediacodec" in available:
                encoder = "h264_mediacodec"
                compute_mode = "android-hardware-mediacodec"
            elif self.config.allow_software_fallback and "libx264" in available:
                encoder = "libx264"
                compute_mode = "android-local-cpu-explicit-fallback"
            else:
                raise AndroidVideoAdapterError(
                    "h264_mediacodec unavailable; CPU fallback is disabled "
                    "(enable allow_software_fallback only after explicit approval)"
                )

            device = self._android_device_info()
            command = [
                "ffmpeg", "-hide_banner", "-y", "-i", str(source),
                "-vf", f"scale={self.config.width}:{self.config.height}:force_original_aspect_ratio=decrease,pad={self.config.width}:{self.config.height}:(ow-iw)/2:(oh-ih)/2,fps={self.config.fps}",
                "-c:v", encoder, "-b:v", self.config.bitrate,
                "-pix_fmt", "nv12" if encoder == "h264_mediacodec" else "yuv420p",
                "-c:a", "aac", "-movflags", "+faststart",
                "-progress", "pipe:1", str(output_path),
            ]
            render = self._run(
                command, timeout=self.config.timeout_seconds,
                capture_output=True, text=True, check=False,
            )
            if render.returncode != 0:
                raise AndroidVideoAdapterError("FFmpeg rendering failed: " + (render.stderr or "")[-1200:])
            if not output_path.is_file() or output_path.stat().st_size <= 0:
                raise AndroidVideoAdapterError("FFmpeg did not produce a non-empty MP4")

            probe = self._run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration,format_name:stream=codec_type,codec_name,width,height",
                 "-of", "json", str(output_path)],
                timeout=30, capture_output=True, text=True, check=False,
            )
            if probe.returncode != 0:
                raise AndroidVideoAdapterError("ffprobe could not validate rendered MP4")
            metadata = json.loads(probe.stdout or "{}")
            streams = metadata.get("streams", [])
            videos = [stream for stream in streams if stream.get("codec_type") == "video"]
            duration = float(metadata.get("format", {}).get("duration", 0))
            if not videos or duration <= 0:
                raise AndroidVideoAdapterError("rendered MP4 has no valid video stream or duration")
            if videos[0].get("codec_name") != "h264":
                raise AndroidVideoAdapterError("rendered video codec is not H.264")

            finished = datetime.now(timezone.utc)
            manifest = {
                "schema_version": "1.0",
                "job_id": job.job_id,
                "adapter": self.name,
                "status": "rendered_qa_pending",
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
                "elapsed_seconds": round(self.clock() - start_clock, 3),
                "compute": {"mode": compute_mode, "encoder": encoder, "device": device},
                "ffmpeg_version": (ffmpeg_version.stdout or "").splitlines()[0],
                "source": {"path": str(source), "size_bytes": source.stat().st_size,
                           "sha256": self._sha256(source)},
                "output": {"path": str(output_path), "size_bytes": output_path.stat().st_size,
                           "sha256": self._sha256(output_path), "duration_seconds": duration,
                           "streams": streams},
                "render_config": asdict(self.config),
                "ffmpeg_exit_code": render.returncode,
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            return AdapterResult(
                True, output_path=str(output_path),
                provider_execution_id=f"{encoder}-{job.job_id}",
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError,
                subprocess.SubprocessError, AndroidVideoAdapterError) as exc:
            output_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
            return AdapterResult(False, error_message=f"{type(exc).__name__}: {exc}")

    def _android_device_info(self) -> dict:
        info = {}
        if shutil.which("getprop") is None:
            return {"platform": "android-assumed-termux", "getprop": "unavailable"}
        for key in ("ro.product.model", "ro.build.version.release",
                    "ro.build.version.sdk", "ro.product.cpu.abi"):
            result = self._run(["getprop", key], timeout=5,
                               capture_output=True, text=True, check=False)
            if result.returncode == 0:
                info[key] = (result.stdout or "").strip()
        return info

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _run(self, command: list[str], **kwargs):
        return self.runner(command, **kwargs)
