# KMH OIA — Hospitality AI Business Intelligence Pilot

Executable Test Pack v0.1. Synthetic training data only; Production HOLD.

Files:
- `sample_hotel_daily.csv`
- `kpi_calculator.py`
- `test_kpi_calculator.py`
- `evidence_report.json`

Run locally:
```bash
python -m unittest -v test_kpi_calculator.py
python kpi_calculator.py sample_hotel_daily.csv
```

Eight local unit tests passed for this package when generated. This is not CI, deployment, independent review, or hotel business-impact evidence.
