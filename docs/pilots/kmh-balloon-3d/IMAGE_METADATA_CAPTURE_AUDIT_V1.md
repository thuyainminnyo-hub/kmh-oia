# KMH_BAL_001 — Image Metadata & Capture Provenance Audit v1.0

## Purpose
Record what the existing image files actually reveal about provenance and define missing metadata needed before calibrated silhouette fitting or photogrammetry.

## Audit result
The audit records SHA-256, pixel dimensions, image format/mode, readable EXIF fields, and conservative semantic classifications. EXIF values, if present, are not independently verified capture facts.

Audit of the 16 available files:
- EXIF-bearing files: 0/16.
- Documented camera poses: 0.
- Documented lens calibration: 0.
- Documented scale references: 0.
- Confirmed per-image visual states: 0.
- Photogrammetry readiness: NOT READY.

EXIF absence does not prove the original capture device lacked metadata; metadata may have been stripped during screenshot, messaging, or export. It means the currently available files contain no readable EXIF.

## Existing image classification
- 16812–16814: original semantic artwork views.
- 16822, 16824: 2019 video frames showing Yan-Khwe as a separate attached visual asset.
- 16826–16842: supplementary video screenshots, not independent calibrated camera stations.
- 16844: ground-laid radial artwork, not bottom-ring dimensional evidence.
- 16850: competition document image, separate document-evidence track.

## Required metadata for each future authorized capture
1. Source file and SHA-256.
2. Capture date/time and time zone; operator role; device and lens.
3. Image dimensions, focal length, camera intrinsics and distortion-calibration reference.
4. Camera station and pose method/reference.
5. Explicit state: BASE-UNLOADED, DISPLAYED-ATTACHED, or UNKNOWN.
6. Scale reference and calibration record, if present.
7. Overlap group and adjacent image references.
8. Lighting, focus, occlusion, subject motion, permission/site-authority reference.
9. Reviewer status and limitations.

## Official methodology references
- [COLMAP tutorial](https://colmap.github.io/tutorial): recommends overlapping images from different viewpoints; each object should be visible in at least three images; rotating from one fixed location is not a substitute for viewpoint diversity.
- [COLMAP camera models](https://colmap.github.io/cameras.html): select the simplest model that adequately represents lens distortion.
- [OpenCV chessboard calibration](https://docs.opencv.org/4.12.0/dc/d43/tutorial_camera_calibration_square_chess.html): camera intrinsic calibration and pose estimation.
- [OpenCV ArUco/ChArUco calibration](https://github.com/opencv/opencv/blob/5.x/doc/tutorials/objdetect/aruco_calibration/aruco_calibration.markdown): calibration from marker corners and multiple viewpoints.
- [Epic RealityScan camera movement](https://dev.epicgames.com/documentation/realityscan-mobile/Photogrammetry-Camera-Movement): systematic capture at different elevations, sharp images, overlap, and limited viewpoint jumps.

These are general methodology references, not evidence that the existing Myanmar balloon images meet those standards.

## Gate
- File metadata audit: COMPLETE for available files.
- Camera pose/lens calibration: NOT DOCUMENTED.
- Scale reference: NOT DOCUMENTED.
- Per-image state attribution: NOT VERIFIED.
- Calibrated silhouette fit: NOT_READY.
- COLMAP photogrammetry: NOT_READY.
- Geometry v2: HOLD.

## Scope and safety
Non-operational visual heritage geometry only. This audit does not authorize physical access, climbing, rigging, touching, moving, loading/unloading, suspending, or modifying the balloon or attachments. Capture must be conducted only by authorized personnel under site authority. It excludes pyrotechnic design, operational calculations, ignition, timing, launch and flight optimization.
