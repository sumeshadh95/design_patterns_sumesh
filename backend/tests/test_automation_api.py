from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def create_location() -> dict:
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
                },
                {
                    "name": "Bench 2",
                    "moisture_threshold_low": 0.1,
                    "moisture_threshold_high": 0.9,
                    "schedule": {},
                },
            ],
        },
    )

    assert response.status_code == 201

    return response.json()


def sensor_in_zone_with_reading(zone_id: str) -> str:
    created = client.post(
        "/api/sensors",
        json={"type": "moisture", "display_name": f"Automation test {uuid4()}"},
    )
    assert created.status_code == 201
    sensor_id = created.json()["id"]

    assert client.patch(
        f"/api/devices/{sensor_id}/zone", json={"zone_id": zone_id}
    ).status_code == 200
    assert client.post(f"/api/sensors/{sensor_id}/read").status_code == 200

    return sensor_id


def test_evaluate_uses_persisted_strategy_key() -> None:
    config = create_location()
    location_id = config["location"]["id"]
    bench_1 = config["zones"][0]["id"]
    sensor_in_zone_with_reading(bench_1)

    save_response = client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "conservative"},
    )

    assert save_response.status_code == 200
    assert save_response.json() == {
        "location_id": location_id,
        "strategy_key": "conservative",
    }

    conservative = client.post(f"/api/locations/{location_id}/automation/evaluate")

    assert conservative.status_code == 200
    assert conservative.json()["strategy_key"] == "conservative"
    assert conservative.json()["action"] == "wait"

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "aggressive"},
    )

    aggressive = client.post(f"/api/locations/{location_id}/automation/evaluate")

    assert aggressive.status_code == 200
    assert aggressive.json()["strategy_key"] == "aggressive"
    assert aggressive.json()["action"] == "irrigate"


def test_evaluate_is_per_zone_and_ignores_other_zones() -> None:
    config = create_location()
    location_id = config["location"]["id"]
    bench_1, bench_2 = (zone["id"] for zone in config["zones"])
    sensor_in_zone_with_reading(bench_1)

    # An unassigned sensor with a fresh reading must not be borrowed.
    loose = client.post("/api/sensors", json={"type": "moisture"}).json()["id"]
    client.post(f"/api/sensors/{loose}/read")

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "aggressive"},
    )
    result = client.post(f"/api/locations/{location_id}/automation/evaluate").json()
    zones = {zone["zone_id"]: zone for zone in result["zones"]}

    assert zones[bench_1]["action"] == "irrigate"
    assert zones[bench_2]["action"] == "wait"
    assert "no moisture" in zones[bench_2]["reason"].lower()


def test_save_unknown_strategy_returns_400() -> None:
    location_id = create_location()["location"]["id"]

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
    response = client.post(f"/api/locations/{uuid4()}/automation/evaluate")

    assert response.status_code == 404
