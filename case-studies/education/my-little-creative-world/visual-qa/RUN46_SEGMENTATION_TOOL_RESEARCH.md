# MLCW V1.0.8 — Run #46 Segmentation Tool Research

**Research date:** 2026-11-02

## Findings

### Meta SAM 3.1 / SAM 2
- Meta's current SAM 3.1 documentation describes concept-based prompts or spatial prompts using boxes and points, returning object masks.
- Meta's SAM 2 project describes promptable image/video segmentation using clicks, boxes or masks, with iterative refinement prompts.
- Potential MLCW experiment: prompt one garment object at a time (blouse, longyi, drape), include positive points inside the intended region and negative points on paper tabs/neighbouring outfits, then compare candidate masks.
- Model predictions still require human edge review; outputs are not production acceptance evidence by themselves.
- No SAM 2 / SAM 3.1 inference was run in Run #46.

### OpenCV GrabCut
- OpenCV's official tutorial describes an initial rectangle around the complete foreground object, followed by iterative segmentation; users can refine by adding foreground/background strokes.
- It may help for clear foreground/background boundaries. It is not a semantic garment parser and may misclassify pale/transparent fabric against white paper.
- GrabCut was researched but not run in Run #46.

### PNG alpha storage
- Pillow's PNG documentation confirms support for RGBA image data and saving PNG files. This validates the storage format used for the candidate alpha channel, not the accuracy of the extracted alpha matte.

## Recommended workflow
1. Try SAM 3.1 or SAM 2 point/box prompts for separate blouse, longyi and drape masks if model inference is available.
2. Add negative prompts at paper tabs and neighbouring outfits.
3. Use a human-reviewed matte for the translucent drape. The flattened RGB PDF cannot uniquely reveal the original transmission alpha.
4. Use GrabCut only as an optional boundary refinement when the foreground/background contrast is clear.
5. Export RGBA PNG layers; inspect on white, dark and saturated backgrounds and at 200% zoom.
6. Keep final P01 composite blocked until layer alignment to Thiri v5 and protected identity-region QA pass.

## Official sources
- Meta SAM 3.1: https://dev.meta.ai/docs/sam/segmenting
- Meta SAM 2: https://ai.meta.com/research/sam2/
- SAM 2 repository: https://github.com/facebookresearch/segment-anything-2
- OpenCV GrabCut: https://docs.opencv.org/4.11.0/d8/d83/tutorial_py_grabcut.html
- OpenCV segmentation API: https://docs.opencv.org/doc/doxygen/html/d3/d47/group__imgproc__segmentation.html
- Pillow PNG docs: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
