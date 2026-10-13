from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def create_location() -> str:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": f"Automation Site {uuid4()}",
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.1,
                    "moisture_threshold_high": 0.9,
                    "schedule": {},
                }
            ],
        },
    )

    assert response.status_code == 201

    return response.json()["location"]["id"]


def take_moisture_reading() -> None:
    create_response = client.post(
        "/api/sensors",
        json={
            "type": "moisture",
            "display_name": f"Automation test {uuid4()}",
        },
    )

    assert create_response.status_code == 201

    sensor_id = create_response.json()["id"]
    read_response = client.post(f"/api/sensors/{sensor_id}/read")

    assert read_response.status_code == 200


def test_evaluate_uses_persisted_strategy_key() -> None:
    location_id = create_location()
    take_moisture_reading()

    save_response = client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "conservative"},
    )

    assert save_response.status_code == 200
    assert save_response.json() == {
        "location_id": location_id,
        "strategy_key": "conservative",
    }

    conservative = client.post(
        f"/api/locations/{location_id}/automation/evaluate"
    )

    assert conservative.status_code == 200
    assert conservative.json()["strategy_key"] == "conservative"
    assert conservative.json()["action"] == "wait"

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "aggressive"},
    )

    aggressive = client.post(
        f"/api/locations/{location_id}/automation/evaluate"
    )

    assert aggressive.status_code == 200
    assert aggressive.json()["strategy_key"] == "aggressive"
    assert aggressive.json()["action"] == "irrigate"


def test_save_unknown_strategy_returns_400() -> None:
    location_id = create_location()

    response = client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "nope"},
    )

    assert response.status_code == 400


def test_save_missing_location_returns_404() -> None:
    response = client.put(
        f"/api/locations/{uuid4()}/automation",
        json={"strategy_key": "conservative"},
    )

    assert response.status_code == 404


def test_evaluate_missing_location_returns_404() -> None:
    response = client.post(
        f"/api/locations/{uuid4()}/automation/evaluate"
    )

    assert response.status_code == 404
