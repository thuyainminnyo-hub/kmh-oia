import json
import unittest
from unittest.mock import patch
from src.earth_observation.stac import AOIValidationError, STACRequestError, search_sentinel2, validate_aoi

VALID_POLYGON = {"type":"Polygon","coordinates":[[[97.0,20.7],[97.01,20.7],[97.01,20.71],[97.0,20.71],[97.0,20.7]]]}

class FakeResponse:
    def __init__(self, payload): self.payload = json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.payload

class AOITests(unittest.TestCase):
    def test_valid_polygon(self):
        self.assertEqual(validate_aoi(VALID_POLYGON), VALID_POLYGON)
    def test_rejects_unclosed_ring(self):
        geometry={"type":"Polygon","coordinates":[[[97,20],[98,20],[98,21],[97,21]]]}
        with self.assertRaises(AOIValidationError): validate_aoi(geometry)
    def test_rejects_out_of_range_coordinates(self):
        geometry={"type":"Polygon","coordinates":[[[197,20],[198,20],[198,21],[197,21],[197,20]]]}
        with self.assertRaises(AOIValidationError): validate_aoi(geometry)
    def test_rejects_point_geometry(self):
        with self.assertRaises(AOIValidationError): validate_aoi({"type":"Point","coordinates":[97,20]})

class STACDiscoveryTests(unittest.TestCase):
    @patch("src.earth_observation.stac.urlopen")
    def test_posts_intersection_and_filters_cloud_cover(self, mock_urlopen):
        mock_urlopen.return_value=FakeResponse({"features":[
            {"id":"clear","properties":{"eo:cloud_cover":12.0}},
            {"id":"cloudy","properties":{"eo:cloud_cover":75.0}}]})
        result=search_sentinel2(VALID_POLYGON,"2026-01-01T00:00:00Z/2026-10-31T23:59:59Z")
        self.assertEqual([x["id"] for x in result],["clear"])
        body=json.loads(mock_urlopen.call_args.args[0].data.decode())
        self.assertEqual(body["collections"],["sentinel-2-l2a"])
        self.assertEqual(body["intersects"],VALID_POLYGON)
    @patch("src.earth_observation.stac.urlopen")
    def test_rejects_missing_features(self,mock_urlopen):
        mock_urlopen.return_value=FakeResponse({"type":"FeatureCollection"})
        with self.assertRaises(STACRequestError):
            search_sentinel2(VALID_POLYGON,"2026-01-01T00:00:00Z/2026-10-31T23:59:59Z")
    def test_rejects_invalid_datetime(self):
        with self.assertRaises(ValueError): search_sentinel2(VALID_POLYGON,"bad")

if __name__=="__main__": unittest.main()
