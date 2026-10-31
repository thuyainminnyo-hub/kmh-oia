import unittest

from src.earth_observation.approval import (
    AOIApprovalError,
    geometry_sha256,
    validate_approved_feature,
)

GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[[97.0, 20.7], [97.01, 20.7], [97.01, 20.71],
                     [97.0, 20.71], [97.0, 20.7]]],
}


def approved_feature():
    return {
        "type": "Feature",
        "geometry": GEOMETRY,
        "properties": {
            "approval_status": "APPROVED",
            "approver_name": "Campus Authorized Representative",
            "approver_role": "Campus Owner Representative",
            "approved_at": "2026-10-31T00:00:00Z",
            "approval_evidence_ref": "restricted://approval/CHINDWIN-001",
            "boundary_source": "authorized-site-plan",
            "boundary_version": "v1",
            "geometry_sha256": geometry_sha256(GEOMETRY),
        },
    }


class AOIApprovalTests(unittest.TestCase):
    def test_accepts_structurally_complete_approved_feature(self):
        self.assertEqual(validate_approved_feature(approved_feature()), GEOMETRY)

    def test_blocks_unapproved_feature(self):
        feature = approved_feature()
        feature["properties"]["approval_status"] = "PROPOSED"
        with self.assertRaises(AOIApprovalError):
            validate_approved_feature(feature)

    def test_blocks_missing_approval_evidence(self):
        feature = approved_feature()
        del feature["properties"]["approval_evidence_ref"]
        with self.assertRaises(AOIApprovalError):
            validate_approved_feature(feature)

    def test_blocks_geometry_tampering(self):
        feature = approved_feature()
        feature["geometry"]["coordinates"][0][1][0] = 97.02
        with self.assertRaises(AOIApprovalError):
            validate_approved_feature(feature)

    def test_blocks_bare_geometry(self):
        with self.assertRaises(AOIApprovalError):
            validate_approved_feature(GEOMETRY)


if __name__ == "__main__":
    unittest.main()
