# KMH OIA Production Module V1 — Local Video Pilot

**Status:** implementation branch / controlled pilot; real GPU execution not yet verified.
**Scope:** one existing source video rendered to H.264 MP4 using local compute. Android MediaCodec via Termux is the phone-first path; NVIDIA NVENC remains an optional desktop adapter.

## Phone-first compute decision

The primary operator environment is Android phone/tablet. Do not require an NVIDIA GPU for the V1 pilot.

- Preferred Android path: Termux + FFmpeg `h264_mediacodec` hardware encoder when exposed by the device/build.
- Explicit fallback: `libx264` CPU encoding is disabled by default and may only be enabled with `--allow-cpu-fallback`.
- Optional desktop path: the existing NVIDIA NVENC adapter remains separate and requires `nvidia-smi` plus `h264_nvenc`.
- Hardware codec availability and stability are device/build dependent. A mocked CI pass is not proof that the phone's codec actually works.

Install in Termux:

```bash
pkg update && pkg upgrade
pkg install python ffmpeg
termux-setup-storage
ffmpeg -hide_banner -encoders | grep -E 'h264_mediacodec|libx264'
ffprobe -version
```

Run from the repository root:

```bash
python -m scripts.run_android_video_pilot --input ~/storage/shared/Movies/source.mp4 --output-dir ~/kmh-oia-output --width 1280 --height 720 --fps 30
```

If the phone does not expose `h264_mediacodec`, the default behavior is HOLD. Only after explicit approval for CPU use, rerun with `--allow-cpu-fallback`. The report must record which encoder actually ran.

## Architecture

`ProductionJob(queued) → ProductionExecutionBridge → AndroidMediaCodecVideoAdapter → FFmpeg/MediaCodec → MP4 + execution manifest → output verification → qa_pending → content QA → human approval`

The existing `ProductionJob` and `ProductionExecutionBridge` remain the job envelope and fail-closed execution boundary. The new adapter is deliberately separate from the image-only ComfyUI adapter.

## V1 guardrails

- Local-only execution; the adapter accepts a local source path and does not call a remote rendering service.
- Android hardware acceleration is explicit: FFmpeg must advertise `h264_mediacodec`; the selected encoder is recorded in the manifest.
- No silent CPU fallback. If MediaCodec is unavailable, the job fails unless the operator explicitly enables `--allow-cpu-fallback`.
- Desktop NVIDIA NVENC is an optional separate adapter, not a V1 phone prerequisite.
- FFmpeg is invoked as an argument array, never through a shell.
- Input must be a non-empty file. Output must be a non-empty MP4 with a valid positive duration and H.264 video stream according to ffprobe.
- Adapter success is not content QA. The bridge must leave the job at `qa_pending`; a separate reviewer must approve it.
- This first slice renders a supplied source video. It does not create 3D models, generate scenes, synthesize voice, author timelines, or perform editorial decisions.

## Implementation tasks

1. [x] Reuse existing immutable ProductionJob contract.
2. [x] Reuse fail-closed ProductionExecutionBridge.
3. [x] Add Android FFmpeg/MediaCodec adapter with explicit CPU fallback approval.
4. [x] Add deterministic unit tests for Android MediaCodec and desktop NVENC adapters.
5. [ ] Add independent content QA (audio/video playback, scene correctness, sync, visual quality).
6. [ ] Add signed/append-only audit persistence and operator identity.
7. [ ] Run exact-head GitHub CI.
8. [ ] Run a real Android MediaCodec smoke test on the operator's phone with a permitted source clip.
9. [ ] Capture real execution manifest, ffprobe output, device/encoder evidence and QA decision.
10. [ ] Obtain human approval before release/promotion.

## Local prerequisites

- Android phone/tablet with Termux.
- FFmpeg exposing `h264_mediacodec` for hardware encoding, or explicit approval for `libx264` CPU fallback.
- `ffprobe` available on PATH.
- A permitted, non-sensitive input video file.
- Python environment with the KMH OIA repository dependencies.

Install and check in Termux:

```bash
pkg update && pkg upgrade
pkg install python ffmpeg
termux-setup-storage
ffmpeg -hide_banner -encoders | grep -E 'h264_mediacodec|libx264'
ffprobe -version
```

Run one controlled Android pilot job (the output directory is also the bridge allowlist):

```bash
python -m scripts.run_android_video_pilot --input ~/storage/shared/Movies/source.mp4 --output-dir ~/kmh-oia-output --width 1280 --height 720 --fps 30
```

If `h264_mediacodec` is unavailable, the job remains HOLD by default. Only after explicit operator approval for local CPU rendering, rerun with `--allow-cpu-fallback`. Desktop NVIDIA NVENC execution remains available through `python -m scripts.run_local_video_pilot`, but is not required for the phone-first pilot.

The command returns `qa_pending` on successful rendering. It never approves or publishes the video. Review the adjacent `.execution.json` manifest and perform the separate content-QA and human-approval steps.

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
