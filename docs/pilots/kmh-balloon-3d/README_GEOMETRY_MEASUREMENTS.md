# Geometry Measurement Register v1.0

Contents:
- `STATE_AWARE_GEOMETRY_MEASUREMENT_PROTOCOL_V1.md`
- `templates/geometry_measurement_record.template.json`
- `templates/profile_measurement_register.template.csv`
- `registry/owner_confirmed_dimensions_v1.json`
- `scripts/validate_geometry_measurement_register.py`

Validate:
```bash
python scripts/validate_geometry_measurement_register.py --dimensions registry/owner_confirmed_dimensions_v1.json --measurements templates/profile_measurement_register.template.csv
```

A pass confirms semantic consistency and template structure only. It does not independently verify the owner-confirmed values. Use only authorized records or measurements by qualified personnel under the relevant site authority. Do not touch, move, load, unload, suspend, or alter the balloon or attached items to obtain measurements.
