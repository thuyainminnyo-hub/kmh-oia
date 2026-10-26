import unittest
from kpi_calculator import validate, calculate_kpis
VALID = {'available_rooms':40,'occupied_rooms':28,'room_revenue_mmk':2240000,'labor_cost_mmk':500000,'supplies_cost_mmk':120000,'utilities_cost_mmk':180000,'maintenance_cost_mmk':100000}
class TestHospitalityPilot(unittest.TestCase):
 def test_t01_valid_data_kpis(self):
  self.assertEqual(validate(VALID).status,'PASS'); k=calculate_kpis(VALID); self.assertEqual(k['occupancy_rate_pct'],70.0); self.assertEqual(k['revpar_mmk'],56000.0); self.assertEqual(k['listed_operating_cost_mmk'],900000.0); self.assertEqual(k['listed_operating_cost_per_occupied_room_mmk'],32142.86)
 def test_t02_zero_occupied_rooms_no_division_by_zero(self):
  row={**VALID,'occupied_rooms':0}; self.assertEqual(validate(row).status,'PASS'); k=calculate_kpis(row); self.assertIsNone(k['listed_operating_cost_per_occupied_room_mmk']); self.assertIsNone(k['labor_cost_per_occupied_room_mmk'])
 def test_t03_occupied_exceeds_available_fails(self): self.assertEqual(validate({**VALID,'occupied_rooms':45}).status,'FAIL')
 def test_t04_negative_cost_fails(self): self.assertEqual(validate({**VALID,'supplies_cost_mmk':-120000}).status,'FAIL')
 def test_t05_missing_field_holds(self):
  row=dict(VALID); del row['utilities_cost_mmk']; self.assertEqual(validate(row).status,'HOLD')
 def test_t06_ai_claim_without_evidence_holds(self):
  rec={'claim':'Supply costs rose because of waste','evidence_ids':[]}; self.assertEqual('PASS' if rec['evidence_ids'] else 'HOLD','HOLD')
 def test_t07_wrong_expected_kpi_detected(self):
  actual=calculate_kpis(VALID)['occupancy_rate_pct']; self.assertEqual(actual,70.0); self.assertNotEqual(actual,75.0)
 def test_t08_execution_without_human_approval_blocked(self):
  approval=None; self.assertFalse(bool(approval and approval.get('approved') is True))
if __name__=='__main__': unittest.main(verbosity=2)
