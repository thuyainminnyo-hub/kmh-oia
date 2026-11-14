import json
import unittest
from pathlib import Path

from src.golden_palace_epcis import (
    parse_receiving_fixture,
    to_epcis_shaped_object_event,
)


FIXTURE = (
    Path(__file__).parent.parent
    / "case-studies/food-traceability/golden-palace-epcis/fixtures/receiving-001.json"
)


class TestGoldenPalaceSyntheticEPCIS(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_is_explicitly_synthetic(self):
        event = parse_receiving_fixture(self.payload)
        self.assertTrue(event.synthetic)
        self.assertEqual(event.product_lot_id, "LOCAL-LOT-RICE-001")
        self.assertEqual(event.quantity, 25.0)

    def test_adapter_emits_object_event_shape_and_local_id(self):
        event = parse_receiving_fixture(self.payload)
        mapped = to_epcis_shaped_object_event(event)
        self.assertEqual(mapped["eventType"], "ObjectEvent")
        self.assertEqual(mapped["action"], "OBSERVE")
        self.assertIn("urn:kmh:oia:synthetic:lot:LOCAL-LOT-RICE-001", mapped["epcList"])
        self.assertEqual(mapped["oiaSyntheticMetadata"]["conformance"], "NOT_CLAIMED")

    def test_rejects_fixture_not_marked_synthetic(self):
        self.payload["synthetic"] = False
        with self.assertRaisesRegex(ValueError, "only explicitly synthetic"):
            parse_receiving_fixture(self.payload)

    def test_rejects_zero_quantity(self):
        self.payload["quantity"] = 0
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            parse_receiving_fixture(self.payload)

    def test_rejects_wrong_event_type(self):
        self.payload["event_type"] = "shipping"
        with self.assertRaisesRegex(ValueError, "must be receiving"):
            parse_receiving_fixture(self.payload)


if __name__ == "__main__":
    unittest.main()
