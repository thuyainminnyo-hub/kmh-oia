"""KMH OIA hospitality KPI calculator v0.1; fictional training data only."""
from dataclasses import dataclass, asdict
from typing import Any

COST_FIELDS = ("labor_cost_mmk", "supplies_cost_mmk", "utilities_cost_mmk", "maintenance_cost_mmk")
REQUIRED_FIELDS = ("available_rooms", "occupied_rooms", "room_revenue_mmk", *COST_FIELDS)

@dataclass
class ValidationResult:
    status: str
    errors: list[str]
    warnings: list[str]

def validate(row: dict[str, Any]) -> ValidationResult:
    missing = [k for k in REQUIRED_FIELDS if k not in row or row[k] is None or row[k] == ""]
    if missing:
        return ValidationResult("HOLD", [f"Missing required fields: {', '.join(missing)}"], [])
    try:
        available, occupied = float(row['available_rooms']), float(row['occupied_rooms'])
        money = [float(row[k]) for k in ("room_revenue_mmk", *COST_FIELDS)]
    except (TypeError, ValueError):
        return ValidationResult("FAIL", ["All inputs must be numeric."], [])
    errors = []
    if available <= 0: errors.append("available_rooms must be greater than zero.")
    if occupied < 0 or occupied > available: errors.append("occupied_rooms must be between zero and available_rooms.")
    if any(x < 0 for x in money): errors.append("Revenue and cost values must be non-negative.")
    return ValidationResult("FAIL" if errors else "PASS", errors, [])

def calculate_kpis(row: dict[str, Any]) -> dict[str, Any]:
    v = validate(row)
    if v.status != "PASS": raise ValueError(f"Cannot calculate KPIs: validation {v.status}: {v.errors}")
    available, occupied = float(row['available_rooms']), float(row['occupied_rooms'])
    revenue = float(row['room_revenue_mmk'])
    total_cost = sum(float(row[k]) for k in COST_FIELDS)
    return {
      "occupancy_rate_pct": round(occupied / available * 100, 2),
      "revpar_mmk": round(revenue / available, 2),
      "listed_operating_cost_mmk": round(total_cost, 2),
      "listed_operating_cost_per_occupied_room_mmk": round(total_cost / occupied, 2) if occupied else None,
      "labor_cost_per_occupied_room_mmk": round(float(row['labor_cost_mmk']) / occupied, 2) if occupied else None,
      "supplies_cost_per_occupied_room_mmk": round(float(row['supplies_cost_mmk']) / occupied, 2) if occupied else None,
      "interpretation_note": "Listed costs only; not net profit; other costs/taxes/commissions may be excluded."
    }

if __name__ == '__main__':
    import csv, json, sys
    p = sys.argv[1] if len(sys.argv) > 1 else 'sample_hotel_daily.csv'
    with open(p, newline='', encoding='utf-8') as f: row = next(csv.DictReader(f))
    for key in REQUIRED_FIELDS: row[key] = float(row[key])
    out = {"validation": asdict(validate(row))}
    if out['validation']['status'] == 'PASS': out['kpis'] = calculate_kpis(row)
    print(json.dumps(out, indent=2))
