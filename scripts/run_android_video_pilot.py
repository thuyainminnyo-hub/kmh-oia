"""Run a controlled local Android MediaCodec video pilot from Termux.

Install prerequisites in Termux with: pkg install python ffmpeg
Run: python -m scripts.run_android_video_pilot --input /sdcard/Movies/source.mp4 --output-dir ~/kmh-oia-output
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.android_video_adapter import AndroidMediaCodecVideoAdapter, AndroidVideoConfig
from src.production_execution import ProductionExecutionBridge
from src.production_job import ProductionJob


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--bitrate", default="6M")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--allow-cpu-fallback", action="store_true",
                        help="Explicitly permit local libx264 CPU encoding if MediaCodec is unavailable")
    parser.add_argument("--prompt", default="Render supplied source video using controlled Android V1 settings")
    args = parser.parse_args()

    output_root = Path(args.output_dir).expanduser().resolve()
    config = AndroidVideoConfig(
        input_path=str(Path(args.input).expanduser().resolve()),
        output_root=str(output_root),
        width=args.width,
        height=args.height,
        fps=args.fps,
        bitrate=args.bitrate,
        allow_software_fallback=args.allow_cpu_fallback,
        timeout_seconds=args.timeout,
    )
    job = ProductionJob.create("video", args.prompt)
    adapter = AndroidMediaCodecVideoAdapter(config)
    result = ProductionExecutionBridge(
        adapter, allowed_output_root=output_root
    ).execute(job)
    report = {
        "job_id": result.job_id,
        "asset_type": result.asset_type,
        "status": result.status,
        "attempt": result.attempt,
        "output_path": result.output_path,
        "provider_execution_id": result.provider_execution_id,
        "error_message": result.error_message,
        "approval": "NOT_GRANTED",
        "next_gate": "independent_content_qa_and_human_approval"
        if result.status == "qa_pending" else "investigate_failure",
    }
    print(json.dumps(report, indent=2))
    return 0 if result.status == "qa_pending" else 1


if __name__ == "__main__":
    raise SystemExit(main())
