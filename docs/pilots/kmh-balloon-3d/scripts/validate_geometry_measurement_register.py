#!/usr/bin/env python3
"""Validate KMH state-aware geometry measurement metadata only."""
import argparse,csv,json
from pathlib import Path
ALLOWED_STATES={"BASE-UNLOADED","DISPLAYED-ATTACHED","UNKNOWN"}
ALLOWED_SEMANTICS={"HEIGHT","WIDTH","DEPTH","CIRCUMFERENCE","DIAMETER","VERTICAL_POSITION"}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dimensions",type=Path,required=True)
 p.add_argument("--measurements",type=Path,required=True)
 a=p.parse_args()
 try: d=json.loads(a.dimensions.read_text(encoding="utf-8"))
 except Exception as e:
  print("FAIL: dimension registry",e); return 2
 expected={
  "OVERALL_ENVELOPE_HEIGHT":("HEIGHT",25,"ft"),
  "MAXIMUM_BODY_CIRCUMFERENCE":("CIRCUMFERENCE",75,"ft"),
  "BOTTOM_RING_DIAMETER":("DIAMETER",7.5,"ft"),
  "TOP_RING_DIAMETER":("DIAMETER",25,"ft")}
 errors=[]
 items={x["feature"]:x for x in d.get("dimensions",[])}
 for feature,(sem,val,unit) in expected.items():
  x=items.get(feature)
  if not x or (x.get("semantic_type"),x.get("value"),x.get("unit"))!=(sem,val,unit):
   errors.append("Missing or semantically inconsistent owner value: "+feature)
  elif x.get("independent_measurement")!="PENDING":
   errors.append("Independent measurement must remain PENDING: "+feature)
 try:
  with a.measurements.open(newline="",encoding="utf-8-sig") as f: rows=list(csv.DictReader(f))
 except Exception as e:
  print("FAIL: measurement CSV",e); return 2
 for i,r in enumerate(rows,2):
  state=(r.get("state_id") or "").strip()
  if state not in ALLOWED_STATES: errors.append(f"Row {i}: invalid state.")
  sem=(r.get("semantic_type") or "").strip()
  if sem and sem not in ALLOWED_SEMANTICS: errors.append(f"Row {i}: invalid semantic type.")
  if (r.get("value") or "").strip():
   for field in ["unit","datum_or_endpoints","method","instrument","observer","measurement_date","uncertainty_or_tolerance","source_evidence"]:
    if not (r.get(field) or "").strip(): errors.append(f"Row {i}: numeric value missing {field}.")
   feature=(r.get("feature") or "").upper()
   if sem=="CIRCUMFERENCE" and "DIAMETER" in feature: errors.append(f"Row {i}: circumference/diameter conflict.")
 if errors:
  print("\n".join("FAIL: "+x for x in errors)); return 1
 print("PASS: four owner-confirmed dimensions retain correct semantic types and pending verification.")
 print("PASS: measurement register schema is valid; no unsupported numeric measurements.")
 print("NOTE: metadata validation only; no physical measurement performed.")
 return 0
if __name__=="__main__": raise SystemExit(main())
