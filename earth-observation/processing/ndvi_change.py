"""Compute a first-pass NDVI difference from locally downloaded, aligned bands.

Inputs must be surface-reflectance Sentinel-2 L2A red (B04) and NIR (B08)
GeoTIFFs for baseline and comparison dates, already clipped to the AOI and
co-registered to the same grid. This is a screening layer, not a final land-cover
classification or proof of change.
"""
import argparse
from pathlib import Path

import numpy as np
import rasterio


def read_band(path):
    with rasterio.open(path) as ds:
        data = ds.read(1).astype("float32")
        profile = ds.profile.copy()
        valid = ds.read_masks(1) > 0
        nodata = ds.nodata
    if nodata is not None:
        valid &= data != nodata
    return data, profile, valid


def ndvi(red, nir):
    denom = nir + red
    out = np.full(red.shape, np.nan, dtype="float32")
    ok = np.isfinite(red) & np.isfinite(nir) & (np.abs(denom) > 1e-6)
    out[ok] = (nir[ok] - red[ok]) / denom[ok]
    return out


def main():
    p = argparse.ArgumentParser()
    for name in ("baseline_red", "baseline_nir", "comparison_red", "comparison_nir", "output"):
        p.add_argument("--" + name.replace("_", "-"), required=True)
    p.add_argument("--threshold", type=float, default=0.20,
                   help="Absolute NDVI difference screening threshold (default 0.20)")
    args = p.parse_args()

    br, bp, brv = read_band(args.baseline_red)
    bn, bnp, bnv = read_band(args.baseline_nir)
    cr, cp, crv = read_band(args.comparison_red)
    cn, cnp, cnv = read_band(args.comparison_nir)
    for label, prof in (("baseline NIR", bnp), ("comparison red", cp), ("comparison NIR", cnp)):
        if prof["crs"] != bp["crs"] or prof["transform"] != bp["transform"] or prof["width"] != bp["width"] or prof["height"] != bp["height"]:
            raise ValueError(f"{label} grid does not match baseline red; warp/resample and co-register first.")

    base = ndvi(br, bn)
    comp = ndvi(cr, cn)
    valid = brv & bnv & crv & cnv & np.isfinite(base) & np.isfinite(comp)
    valid_fraction = float(valid.mean())
    if valid_fraction < 0.80:
        raise RuntimeError(f"Only {valid_fraction:.1%} valid comparable pixels; minimum is 80%.")
    delta = np.full(base.shape, -9999.0, dtype="float32")
    delta[valid] = comp[valid] - base[valid]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    profile = bp.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, nodata=-9999.0, compress="deflate")
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(delta, 1)
        dst.set_band_description(1, "NDVI difference (comparison minus baseline)")
        dst.update_tags(
            method="NDVI difference screening",
            threshold=str(args.threshold),
            valid_pixel_fraction=str(valid_fraction),
            interpretation="Candidate vegetation signal change; requires cloud/shadow QA and human review",
        )
    changed = valid & (np.abs(delta) >= args.threshold)
    print({
        "output": str(out),
        "valid_comparable_pixel_fraction": round(valid_fraction, 4),
        "ndvi_change_threshold": args.threshold,
        "candidate_changed_pixel_fraction_of_valid": round(float(changed.sum() / valid.sum()), 4),
        "classification_status": "screening_only_not_validated",
    })


if __name__ == "__main__":
    main()
