from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def create_location(name: str) -> str:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": name,
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


def take_moisture_reading() -> str:
    create_response = client.post(
        "/api/sensors",
        json={
            "type": "moisture",
            "display_name": f"Overview test {uuid4()}",
        },
    )

    assert create_response.status_code == 201

    sensor_id = create_response.json()["id"]
    read_response = client.post(f"/api/sensors/{sensor_id}/read")

    assert read_response.status_code == 200

    return sensor_id


def test_overview_returns_strategy_and_readings() -> None:
    location_name = f"Overview Site {uuid4()}"
    location_id = create_location(location_name)
    sensor_id = take_moisture_reading()

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "aggressive"},
    )

    response = client.get(f"/api/locations/{location_id}/overview")

    assert response.status_code == 200

    overview = response.json()

    assert set(overview) == {
        "location",
        "device_counts",
        "latest_readings",
        "strategy_key",
        "last_recommendation",
    }
    assert overview["location"] == {"id": location_id, "name": location_name}
    assert overview["device_counts"]["sensor"] >= 1
    assert overview["device_counts"]["actuator"] >= 0
    assert overview["strategy_key"] == "aggressive"
    assert overview["last_recommendation"]["action"] == "irrigate"
    assert overview["last_recommendation"]["reason"]

    reading = overview["latest_readings"][0]

    assert reading["device_id"] == sensor_id
    assert reading["unit"] == "vwc"
    assert set(reading) == {"device_id", "value", "unit", "recorded_at"}


def test_overview_reflects_strategy_change() -> None:
    location_id = create_location(f"Overview Site {uuid4()}")
    take_moisture_reading()

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "conservative"},
    )
    conservative = client.get(f"/api/locations/{location_id}/overview").json()

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "aggressive"},
    )
    aggressive = client.get(f"/api/locations/{location_id}/overview").json()

    assert conservative["strategy_key"] == "conservative"
    assert conservative["last_recommendation"]["action"] == "wait"
    assert aggressive["strategy_key"] == "aggressive"
    assert aggressive["last_recommendation"]["action"] == "irrigate"


def test_overview_missing_location_returns_404() -> None:
    response = client.get(f"/api/locations/{uuid4()}/overview")

    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found."
