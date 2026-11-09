# KMH-BAL-001 — Supplemental Visual Evidence Inventory v1

Status: INGESTED AS REFERENCE EVIDENCE; NOT A PHOTOGRAMMETRY DATASET.

## Source and limitations

Twelve user-uploaded JPEG screenshots were received on 2026-11-09. All are 1845 × 2048 pixels. They are screenshots of video playback / social-media UI, not original camera files. They include overlays and compression; EXIF camera calibration metadata is not established. SHA-256 values below identify the exact received files.

The set appears to contain:
- Exterior rotating/inflation sequence frames: 16826, 16828, 16830, 16832, 16834, 16836, 16838, 16840, 16842.
- Laid-flat lower/fabric panel view: 16844.
- Historical internal framework / lighting reference from a separately displayed 2019 Channel Taunggyi clip: 16822, 16824.

Do not assume the 2019 internal-framework reference depicts the exact same balloon asset or build configuration. Treat it as contextual structural reference only until provenance is confirmed.

## What these references support

- Exterior silhouette and approximate proportion observations across changing viewpoints.
- Artwork segmentation: fiery orange/red/black text panel; Buddha and narrative artwork; lower radial ornament.
- A useful view of the lower fabric panel laid flat (16844).
- Contextual observations of internal support / lighting arrangements in the 2019 clip (16822, 16824).

## What they do NOT establish

- Calibrated camera poses, focal lengths, scale, or a complete 360-degree image set.
- Exact physical height, width, depth, envelope volume, or material thickness.
- Exact identity of the 2019 internal framework relative to KMH-BAL-001.
- A production-ready texture atlas, UV map, or photogrammetric reconstruction.

## File integrity manifest

| File | SHA-256 |
|---|---|
| 16842.jpg | 7e67ba8542975e398348d3f9d18f366729950e6934ab59aabf5b272f8f9e0d93 |
| 16840.jpg | 0c40282e16f5ff9960befb45700fe479c808048a10579609023f6e26975a3042 |
| 16838.jpg | fa37ac034356a22ef621939b68f890444e08c92833a63d2fcaf4c58d01039b8f |
| 16836.jpg | afaf09f8ba40a9bfaf5b7f1806000fba9ab235022f5da317a4747fefa33c6769 |
| 16834.jpg | 1735e3dbbe649a5f8a56175b39dbdf6712e37d45fad218871acac5ab26855c60 |
| 16832.jpg | 0820458db67579bbf0b0c0663306696ed6174e74410af8a1be9237a9aef4e7b2 |
| 16830.jpg | c7921e4a84913187b12ac5bd784e1f1642b4355e2a95eceb4fb291b9bec89b48 |
| 16828.jpg | f36e05ce87ed8cfc3687c258b6ab90e74d9c4bbfdcaa0b49646565f66616f8e8 |
| 16826.jpg | 3c71bd9ec1f1890482cd2ea82964d0c9b8b1585356891d158d43f27dee5fc6c8 |
| 16824.jpg | cbe0f4f6386e6e1cfe3b46bf4d0079c4a83112a4773b5814913cb952bfe197a8 |
| 16822.jpg | 0331500dc001098d64a847fa927c0235862a715f6b83a8b3f2b174ea6d9e6f42 |
| 16844.jpg | 26e9e470020a73e81af1d3b90730f2b7659f0f0f85fa9b93712502cf81b9f86e |

## Dataset decision

Keep these files in a supplemental reference collection, separate from any future original camera capture dataset. For Tripo multiview, manually select and crop clean exterior views only after confirming view orientation. For COLMAP, do not feed social-media screenshot frames as if they were calibrated original photos; obtain original video or a fresh overlapping camera capture set.

## Next capture requirements

1. Obtain the original source video (not screen recordings/screenshots), if available.
2. Capture clean, non-overlaid frames at distinct azimuths; avoid near-duplicate frames.
3. Record whether the 2019 internal framework clip belongs to this same balloon.
4. Capture top, bottom opening, seams, attachment points, and internal frame in close detail.
5. Keep physical measurements and their uncertainty in a separate measurement record.
