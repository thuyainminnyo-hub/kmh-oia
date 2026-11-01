# MLCW V1.0.8 — Run #33 Asset Inspection

**Result:** 12 uploaded source files identified: one canonical Thiri identity reference, ten outfit concept panels and one accessory strip.

## Character identity reference

- `15309(1).png` — 1024×1536 RGBA; 0% transparent.
- Shows Thiri in the cream blouse and longyi with dark hair bun, white flower and gold earrings.
- This is the canonical identity reference, **not** a clean body base: it is fully opaque and the clothing hides parts of the body that cannot be recovered by simply erasing pixels.

## Outfit catalog — working slots and observed source content

| Working slot | File | Observed design | Alpha transparent | Largest component share | Edge touch |
|---|---|---|---:|---:|---|
| P01 | `15312(1).png` | Gold blouse, ruby/red longyi, cream-gold shawl | 36.346% | 96.428% | Left + bottom |
| P02 | `15311(1).png` | Cream blouse, blue longyi, blue shawl | 32.394% | 66.822% | Left + bottom |
| P03 | `15310(1).png` | Light-blue blouse, navy longyi, blue shawl | 34.875% | 99.767% | Left + bottom |
| P04 | `15308(1).png` | Green blouse, dark-green longyi, green shawl | 38.663% | 99.103% | Left + right + bottom |
| P05 | `15307(1).png` | Pink outfit with ruffled shawl | 32.436% | 67.960% | Left + bottom |
| P06 | `15306(1).png` | Lavender blouse, purple longyi | 36.765% | 96.770% | Left + bottom |
| P07 | `15305(1).png` | Ornate cream/gold/pink formal outfit | 33.487% | 99.507% | Left + right + bottom |
| P08 | `15303(1).png` | Pink blouse, magenta longyi | 35.684% | 98.538% | Left + bottom |
| P09 | `15302(1).png` | Teal blouse, turquoise longyi | 39.644% | 96.634% | Left + bottom |
| P10 | `15301(1).png` | Coral blouse, brown longyi | 32.078% | 86.586% | Left + bottom |

All ten largest alpha components touch the left and bottom canvas edges. P02, P05 and P10 have substantial second components (21,617; 20,872; 8,523 pixels respectively), indicating neighboring outfit fragments in the panels. P01 has a 1,875-pixel second component corresponding to the adjacent purple outfit fragment.

**Catalog integrity:** P01–P10 are provisional production working slots. Do not equate them with legacy `MLCW-OUTFIT-001..010` identifiers based on order alone. Reconcile the file-to-registry mapping before publishing the master catalog.

## P01 connected-component inspection

- File: `15312(1).png` — 225×431 RGBA.
- Transparent pixels: 36.346%; non-transparent: 61,728.
- Connected components: 75.
- Largest component: 59,523 pixels (96.428% of all non-transparent pixels); bounding box `[0,18,189,431]`; touches left and bottom edges.
- Second largest component: 1,875 pixels; bounding box `[194,85,225,205]`; neighboring purple outfit fragment.
- Largest-alpha-component cutout is a diagnostic candidate only. It does not reconstruct missing clipped pixels and does not prove tabs/edges have been cleanly removed.

## Accessory sheet

- `15304(1).png` — 1536×169 RGB; opaque, no alpha channel.
- Near-white pixels: 58.013%.
- Contains flowers, hair ornaments, decorative headpieces, handbags and shoes. Each object needs segmentation, transparency extraction and human edge review.

## Gate decision

**INTAKE: PASS** — all 12 source files were located and inspected.  
**PRODUCTION ASSET READINESS: HOLD** — a separate clean body base, uncropped P01 garment layers and separated transparent accessory assets are not yet available.  
**No actual Thiri/P01 outfit composite or protected-pixel identity QA has been performed in this inspection.**

## Diagnostic outputs

Diagnostic alpha masks, connected-component cutout candidates and image contact sheet are retained separately in the Run #33 asset inspection package. They are not approved production layers.
