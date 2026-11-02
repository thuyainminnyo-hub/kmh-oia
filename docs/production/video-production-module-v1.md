# KMH OIA Production Module V1 — Local Video Pilot

**Status:** implementation branch / controlled pilot; real GPU execution not yet verified.
**Scope:** one existing source video rendered to H.264 MP4 using local NVIDIA NVENC through FFmpeg.

## Architecture

`ProductionJob(queued) → ProductionExecutionBridge → LocalFFmpegVideoAdapter → FFmpeg/NVENC → MP4 + execution manifest → output verification → qa_pending → content QA → human approval`

The existing `ProductionJob` and `ProductionExecutionBridge` remain the job envelope and fail-closed execution boundary. The new adapter is deliberately separate from the image-only ComfyUI adapter.

## V1 guardrails

- Local-only execution; the adapter accepts a local source path and does not call a remote rendering service.
- NVIDIA GPU acceleration is explicit: `nvidia-smi` must identify a GPU and FFmpeg must advertise `h264_nvenc`.
- No silent CPU fallback. If NVENC is unavailable, the job fails before rendering.
- FFmpeg is invoked as an argument array, never through a shell.
- Input must be a non-empty file. Output must be a non-empty MP4 with a valid positive duration and H.264 video stream according to ffprobe.
- Adapter success is not content QA. The bridge must leave the job at `qa_pending`; a separate reviewer must approve it.
- This first slice renders a supplied source video. It does not create 3D models, generate scenes, synthesize voice, author timelines, or perform editorial decisions.

## Implementation tasks

1. [x] Reuse existing immutable ProductionJob contract.
2. [x] Reuse fail-closed ProductionExecutionBridge.
3. [x] Add local FFmpeg/NVENC adapter with explicit no-CPU-fallback behavior.
4. [x] Add deterministic unit tests with mocked system commands.
5. [ ] Add independent content QA (audio/video playback, scene correctness, sync, visual quality).
6. [ ] Add signed/append-only audit persistence and operator identity.
7. [ ] Run exact-head GitHub CI.
8. [ ] Run a real local GPU smoke test on the operator's machine with a permitted source clip.
9. [ ] Capture real execution manifest, ffprobe output, GPU evidence and QA decision.
10. [ ] Obtain human approval before release/promotion.

## Local prerequisites

- NVIDIA GPU and compatible driver.
- FFmpeg build that includes `h264_nvenc`.
- `ffprobe` available on PATH.
- A permitted, non-sensitive input video file.
- Python environment with the KMH OIA repository dependencies.

Check readiness:

```bash
nvidia-smi
ffmpeg -hide_banner -encoders | grep h264_nvenc
ffprobe -version
```

A missing GPU/encoder must remain a HOLD; do not switch to CPU and label it a GPU run.\n\nRun one controlled pilot job (the output directory is also the bridge allowlist):\n\n```bash\npython -m scripts.run_local_video_pilot --input media/source.mp4 --output-dir artifacts/video --width 1920 --height 1080 --fps 30\n```\n\nThe command returns `qa_pending` on successful rendering. It never approves or publishes the video. Review the adjacent `.execution.json` manifest and perform the separate content-QA and human-approval steps.

## Evidence contract

For each real run retain:
- Job ID, commit SHA, adapter version and UTC timestamps.
- Source file SHA-256 and byte size (written to the execution manifest).
- GPU model and driver version from `nvidia-smi`.
- FFmpeg version and explicit NVENC encoder selection.
- FFmpeg exit code and elapsed time.
- Output MP4 SHA-256, byte size, duration, dimensions and stream metadata from ffprobe (written to the execution manifest).
- QA report covering playback, audio sync, visual correctness and requested brief.
- Named human approver, decision, timestamp and revision reference.

Do not place source media, secrets, private paths or personal data in public CI artifacts.

## CI vs real execution

GitHub-hosted CI runs deterministic tests with mocked FFmpeg/NVIDIA probes. It validates contracts and failure behavior, not GPU access or real rendering. Real local GPU verification is a separate operator-run gate and is not claimed by CI.

## Release decision

**HOLD** until exact-head CI passes, a real local NVENC render is evidenced, independent content QA passes, and a human explicitly approves the output.
