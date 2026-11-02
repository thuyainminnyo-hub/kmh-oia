"""Controlled local FFmpeg/NVIDIA NVENC video renderer.

This adapter deliberately requires an explicitly available NVIDIA NVENC encoder.
It never silently falls back to CPU encoding. It produces a rendered MP4 and a
machine-readable execution manifest; content QA and human approval remain
separate gates.
"""
from __future__ import annotations

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


class LocalVideoAdapterError(RuntimeError):
    """Raised when local video rendering prerequisites or outputs are invalid."""


@dataclass(frozen=True)
class VideoRenderConfig:
    input_path: str
    output_root: str
    width: int = 1920
    height: int = 1080
    fps: int = 30
    video_codec: str = "h264_nvenc"
    preset: str = "p4"
    audio_codec: str = "aac"
    timeout_seconds: int = 1800

    def __post_init__(self) -> None:
        if not self.input_path or not self.output_root:
            raise ValueError("input_path and output_root are required")
        if self.width < 2 or self.height < 2 or self.width % 2 or self.height % 2:
            raise ValueError("width and height must be positive even integers")
        if not 1 <= self.fps <= 120:
            raise ValueError("fps must be between 1 and 120")
        if self.video_codec != "h264_nvenc":
            raise ValueError("V1 requires h264_nvenc; CPU fallback is not permitted")
        if self.preset not in {"p1", "p2", "p3", "p4", "p5", "p6", "p7"}:
            raise ValueError("unsupported NVENC preset")
        if self.audio_codec != "aac":
            raise ValueError("V1 supports AAC audio only")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


class LocalFFmpegVideoAdapter:
    """Render one local source video with explicit NVIDIA NVENC acceleration."""

    name = "local-ffmpeg-nvenc"

    def __init__(
        self,
        config: VideoRenderConfig,
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
            return AdapterResult(False, error_message="video adapter only supports video jobs")
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
                raise LocalVideoAdapterError("input video must be an existing non-empty file")
            if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
                raise LocalVideoAdapterError("ffmpeg and ffprobe must both be installed")
            gpu = self._probe_gpu()
            encoders = self._run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                timeout=30,
                capture_output=True,
                text=True,
                check=False,
            )
            if encoders.returncode != 0 or "h264_nvenc" not in (encoders.stdout or ""):
                raise LocalVideoAdapterError("FFmpeg h264_nvenc encoder is unavailable; refusing CPU fallback")

            command = [
                "ffmpeg", "-hide_banner", "-y", "-i", str(source),
                "-vf", f"scale={self.config.width}:{self.config.height}:force_original_aspect_ratio=decrease,pad={self.config.width}:{self.config.height}:(ow-iw)/2:(oh-ih)/2,fps={self.config.fps}",
                "-c:v", self.config.video_codec, "-preset", self.config.preset,
                "-pix_fmt", "yuv420p", "-c:a", self.config.audio_codec,
                "-movflags", "+faststart", "-progress", "pipe:1", str(output_path),
            ]
            render = self._run(
                command,
                timeout=self.config.timeout_seconds,
                capture_output=True,
                text=True,
                check=False,
            )
            if render.returncode != 0:
                raise LocalVideoAdapterError("FFmpeg rendering failed: " + (render.stderr or "")[-1200:])
            if not output_path.is_file() or output_path.stat().st_size <= 0:
                raise LocalVideoAdapterError("FFmpeg did not produce a non-empty MP4")
            probe = self._run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration,format_name:stream=codec_type,codec_name,width,height",
                 "-of", "json", str(output_path)],
                timeout=30,
                capture_output=True,
                text=True,
                check=False,
            )
            if probe.returncode != 0:
                raise LocalVideoAdapterError("ffprobe could not validate rendered MP4")
            metadata = json.loads(probe.stdout or "{}")
            streams = metadata.get("streams", [])
            video_streams = [item for item in streams if item.get("codec_type") == "video"]
            duration = float(metadata.get("format", {}).get("duration", 0))
            if not video_streams or duration <= 0:
                raise LocalVideoAdapterError("rendered MP4 has no valid video stream or duration")
            if video_streams[0].get("codec_name") != "h264":
                raise LocalVideoAdapterError("rendered video codec is not H.264")
            finished = datetime.now(timezone.utc)
            manifest = {
                "schema_version": "1.0",
                "job_id": job.job_id,
                "adapter": self.name,
                "status": "rendered_qa_pending",
                "started_at": started.isoformat(),
                "finished_at": finished.isoformat(),
                "elapsed_seconds": round(self.clock() - start_clock, 3),
                "compute": {"requested": "nvidia-nvenc", "gpu_probe": gpu,
                            "encoder": self.config.video_codec},
                "source": {"path": str(source), "size_bytes": source.stat().st_size},
                "output": {"path": str(output_path), "size_bytes": output_path.stat().st_size,
                           "duration_seconds": duration, "streams": streams},
                "render_config": asdict(self.config),
                "ffmpeg_exit_code": render.returncode,
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            return AdapterResult(
                True, output_path=str(output_path),
                provider_execution_id=f"local-nvenc-{job.job_id}",
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError,
                subprocess.SubprocessError, LocalVideoAdapterError) as exc:
            output_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
            return AdapterResult(False, error_message=f"{type(exc).__name__}: {exc}")

    def _probe_gpu(self) -> dict:
        if shutil.which("nvidia-smi") is None:
            raise LocalVideoAdapterError("nvidia-smi not found; NVIDIA GPU evidence is required")
        result = self._run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            timeout=15, capture_output=True, text=True, check=False,
        )
        if result.returncode != 0 or not (result.stdout or "").strip():
            raise LocalVideoAdapterError("nvidia-smi could not identify an available NVIDIA GPU")
        return {"nvidia_smi": (result.stdout or "").strip()}

    def _run(self, command: list[str], **kwargs):
        return self.runner(command, **kwargs)
