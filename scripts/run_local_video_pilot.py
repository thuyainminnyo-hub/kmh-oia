"""Run one controlled local NVIDIA NVENC video pilot job.

Example:
  python -m scripts.run_local_video_pilot --input media/source.mp4 --output-dir artifacts/video
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.local_video_adapter import LocalFFmpegVideoAdapter, VideoRenderConfig
from src.production_execution import ProductionExecutionBridge
from src.production_job import ProductionJob


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Existing local source video")
    parser.add_argument("--output-dir", required=True, help="Allowed output directory")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--prompt", default="Render supplied source video using approved V1 settings")
    args = parser.parse_args()

    output_root = Path(args.output_dir).resolve()
    config = VideoRenderConfig(
        input_path=str(Path(args.input).resolve()),
        output_root=str(output_root),
        width=args.width,
        height=args.height,
        fps=args.fps,
        timeout_seconds=args.timeout,
    )
    job = ProductionJob.create("video", args.prompt)
    adapter = LocalFFmpegVideoAdapter(config)
    bridge = ProductionExecutionBridge(adapter, allowed_output_root=output_root)
    result = bridge.execute(job)

    report = {
        "job_id": result.job_id,
        "asset_type": result.asset_type,
        "status": result.status,
        "attempt": result.attempt,
        "output_path": result.output_path,
        "provider_execution_id": result.provider_execution_id,
        "error_message": result.error_message,
        "approval": "NOT_GRANTED",
        "next_gate": "independent_content_qa_and_human_approval" if result.status == "qa_pending" else "investigate_failure",
    }
    print(json.dumps(report, indent=2))
    return 0 if result.status == "qa_pending" else 1


if __name__ == "__main__":
    raise SystemExit(main())
