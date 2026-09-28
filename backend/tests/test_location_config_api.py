from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_get_location_config() -> None:
    location_name = f"Integration Site {uuid4()}"

    create_response = client.post(
        "/api/locations/config",
        json={
            "location_name": location_name,
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.45,
                    "schedule": {"watering": "08:00"},
                },
                {
                    "name": "Bench 2",
                    "moisture_threshold_low": 0.25,
                    "moisture_threshold_high": 0.5,
                    "schedule": {"watering": "18:00"},
                },
            ],
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()
    location_id = created["location"]["id"]

    assert created["location"]["name"] == location_name
    assert len(created["zones"]) == 2
    assert all(zone["location_id"] == location_id for zone in created["zones"])

    get_response = client.get(f"/api/locations/{location_id}/config")

    assert get_response.status_code == 200

    fetched = get_response.json()

    assert fetched["location"]["id"] == location_id
    assert fetched["location"]["name"] == location_name
    assert len(fetched["zones"]) == 2
    assert all(zone["location_id"] == location_id for zone in fetched["zones"])


def test_create_location_config_rejects_invalid_threshold_order() -> None:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": "Invalid Site",
            "zones": [
                {
                    "name": "Bad Bench",
                    "moisture_threshold_low": 0.7,
                    "moisture_threshold_high": 0.4,
                    "schedule": {},
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "lower" in response.json()["detail"]


def test_get_missing_location_config_returns_404() -> None:
    response = client.get(f"/api/locations/{uuid4()}/config")

    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found."