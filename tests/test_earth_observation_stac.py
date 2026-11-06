import json
import unittest
from unittest.mock import patch

from src.earth_observation.stac import (
    AOIValidationError,
    STACRequestError,
    search_sentinel2,
    validate_aoi,
)

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[97.0, 20.7], [97.01, 20.7], [97.01, 20.71],
                     [97.0, 20.71], [97.0, 20.7]]],
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class AOITests(unittest.TestCase):
    def test_valid_polygon(self):
        self.assertEqual(validate_aoi(VALID_POLYGON), VALID_POLYGON)

    def test_rejects_unclosed_ring(self):
        geometry = {"type": "Polygon", "coordinates": [
            [[97, 20], [98, 20], [98, 21], [97, 21]]
        ]}
        with self.assertRaises(AOIValidationError):
            validate_aoi(geometry)

    def test_rejects_out_of_range_coordinates(self):
        geometry = {"type": "Polygon", "coordinates": [
            [[197, 20], [198, 20], [198, 21], [197, 21], [197, 20]]
        ]}
        with self.assertRaises(AOIValidationError):
            validate_aoi(geometry)

    def test_rejects_point_geometry(self):
        with self.assertRaises(AOIValidationError):
            validate_aoi({"type": "Point", "coordinates": [97, 20]})


class STACDiscoveryTests(unittest.TestCase):
    @patch("src.earth_observation.stac.urlopen")
    def test_posts_intersection_and_filters_cloud_cover(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"features": [
            {"id": "clear", "properties": {"eo:cloud_cover": 12.0}},
            {"id": "cloudy", "properties": {"eo:cloud_cover": 75.0}},
            {"id": "unknown", "properties": {}},
        ]})
        result = search_sentinel2(
            VALID_POLYGON, "2026-01-01T00:00:00Z/2026-10-31T23:59:59Z"
        )
        self.assertEqual([item["id"] for item in result], ["clear"])
        request = mock_urlopen.call_args.args[0]
        body = json.loads(request.data.decode())
        self.assertEqual(request.full_url,
                         "https://stac.opensearch.dataspace.copernicus.eu/v1/search")
        self.assertEqual(body["collections"], ["sentinel-2-l2a"])
        self.assertEqual(body["intersects"], VALID_POLYGON)
        self.assertEqual(request.get_method(), "POST")

    @patch("src.earth_observation.stac.urlopen")
    def test_follows_next_page(self, mock_urlopen):
        next_url = (
            "https://stac.opensearch.dataspace.copernicus.eu/v1/search?token=page2"
        )
        mock_urlopen.side_effect = [
            FakeResponse({"features": [
                {"id": "page-1", "properties": {"eo:cloud_cover": 10}}
            ], "links": [{"rel": "next", "href": next_url}]}),
            FakeResponse({"features": [
                {"id": "page-2", "properties": {"eo:cloud_cover": 20}}
            ]}),
        ]
        result = search_sentinel2(
            VALID_POLYGON, "2026-01-01T00:00:00Z/2026-10-31T23:59:59Z"
        )
        self.assertEqual([item["id"] for item in result], ["page-1", "page-2"])
        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertEqual(mock_urlopen.call_args_list[1].args[0].get_method(), "GET")

    @patch("src.earth_observation.stac.urlopen")
    def test_rejects_external_pagination_link(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"features": [], "links": [
            {"rel": "next", "href": "https://example.com/steal"}
        ]})
        with self.assertRaises(STACRequestError):
            search_sentinel2(
                VALID_POLYGON, "2026-01-01T00:00:00Z/2026-10-31T23:59:59Z"
            )

    @patch("src.earth_observation.stac.urlopen")
    def test_rejects_missing_features(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse({"type": "FeatureCollection"})
        with self.assertRaises(STACRequestError):
            search_sentinel2(
                VALID_POLYGON, "2026-01-01T00:00:00Z/2026-10-31T23:59:59Z"
            )

    def test_rejects_invalid_datetime(self):
        with self.assertRaises(ValueError):
            search_sentinel2(VALID_POLYGON, "bad")

from src.earth_observation.aoi_approval import (
    AOIApprovalError,
    geometry_sha256,
    require_approved_aoi,
    search_approved_campus_aoi,
)
from src.earth_observation.assets import AssetValidationError, validate_l2a_assets


class AOIApprovalGateTests(unittest.TestCase):
    def approved_record(self):
        return {
            "aoi_id": "chindwin-taunggyi-campus-v1",
            "status": "APPROVED",
            "crs": "EPSG:4326",
            "geometry": VALID_POLYGON,
            "geometry_sha256": geometry_sha256(VALID_POLYGON),
            "approved_by": "Authorized Campus Representative",
            "approved_at": "2026-11-06T09:00:00+06:30",
            "approval_evidence_uri": "https://example.org/approval/evidence",
        }

    def test_accepts_complete_approved_record(self):
        self.assertEqual(require_approved_aoi(self.approved_record())["status"], "APPROVED")

    def test_rejects_missing_approval(self):
        record = self.approved_record()
        record["status"] = "PENDING"
        with self.assertRaises(AOIApprovalError):
            require_approved_aoi(record)

    def test_rejects_geometry_hash_mismatch(self):
        record = self.approved_record()
        record["geometry"] = {
            "type": "Polygon",
            "coordinates": [[[97, 20], [97.02, 20], [97.02, 20.02],
                             [97, 20.02], [97, 20]]],
        }
        with self.assertRaises(AOIApprovalError):
            require_approved_aoi(record)

    def test_rejects_missing_approver(self):
        record = self.approved_record()
        record["approved_by"] = ""
        with self.assertRaises(AOIApprovalError):
            require_approved_aoi(record)

    @patch("src.earth_observation.stac.urlopen")
    def test_pending_aoi_is_rejected_before_network_request(self, mock_urlopen):
        record = self.approved_record()
        record["status"] = "PENDING"
        with self.assertRaises(AOIApprovalError):
            search_approved_campus_aoi(
                record, "2026-01-01T00:00:00Z/2026-11-06T23:59:59Z"
            )
        mock_urlopen.assert_not_called()

    def test_rejects_non_https_evidence(self):
        record = self.approved_record()
        record["approval_evidence_uri"] = "file:///tmp/approval"
        with self.assertRaises(AOIApprovalError):
            require_approved_aoi(record)


class L2AAssetValidationTests(unittest.TestCase):
    def valid_item(self):
        return {"assets": {
            key: {
                "type": "image/jp2",
                "roles": ["data", "reflectance"],
                "gsd": gsd,
                "file:size": 1000,
                "file:checksum": "sha256:abc123",
                "href": f"s3://example/{key}.jp2",
            }
            for key, gsd in {
                "B04_10m": 10, "B08_10m": 10, "SCL_20m": 20
            }.items()
        }}

    def test_accepts_required_l2a_assets(self):
        self.assertEqual(len(validate_l2a_assets(self.valid_item())), 3)

    def test_rejects_missing_nir_band(self):
        item = self.valid_item()
        del item["assets"]["B08_10m"]
        with self.assertRaises(AssetValidationError):
            validate_l2a_assets(item)

    def test_rejects_wrong_resolution(self):
        item = self.valid_item()
        item["assets"]["SCL_20m"]["gsd"] = 10
        with self.assertRaises(AssetValidationError):
            validate_l2a_assets(item)

    def test_rejects_missing_checksum(self):
        item = self.valid_item()
        del item["assets"]["B04_10m"]["file:checksum"]
        with self.assertRaises(AssetValidationError):
            validate_l2a_assets(item)


if __name__ == "__main__":
    unittest.main()
