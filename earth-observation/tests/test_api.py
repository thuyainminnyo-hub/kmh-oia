from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog_rejects_invalid_geometry():
    response = client.post(
        "/v1/catalog/sentinel-2/search",
        json={
            "aoi": {"type": "Point", "coordinates": [96.1, 16.8]},
            "start_date": "2025-01-01",
            "end_date": "2025-02-01",
        },
    )
    assert response.status_code == 422


def test_catalog_rejects_reversed_dates():
    response = client.post(
        "/v1/catalog/sentinel-2/search",
        json={
            "aoi": {
                "type": "Polygon",
                "coordinates": [[[96, 16], [96.1, 16], [96.1, 16.1], [96, 16.1], [96, 16]]],
            },
            "start_date": "2025-02-01",
            "end_date": "2025-01-01",
        },
    )
    assert response.status_code == 422
