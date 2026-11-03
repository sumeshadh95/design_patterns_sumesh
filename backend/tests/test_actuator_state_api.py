from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def provisioned() -> list[dict]:
    response = client.post("/api/devices/provision?family=simulation")

    assert response.status_code == 201

    return response.json()


def find(devices: list[dict], device_type: str) -> dict:
    return next(d for d in devices if d["device_type"] == device_type)


def current(device_id: str) -> dict:
    devices = client.get("/api/devices?role=actuator").json()

    return next(d for d in devices if d["id"] == device_id)


def transition(device_id: str, target: str):
    return client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": target},
    )


def test_provisioned_actuators_start_idle(provisioned: list[dict]) -> None:
    pump = find(provisioned, "water_pump")
    light = find(provisioned, "grow_light")
    sensor = find(provisioned, "moisture_sensor")

    assert pump["state"] == "idle"
    assert pump["allowed_commands"] == ["start_pump"]
    assert light["state"] == "idle"
    assert light["allowed_commands"] == ["set_light_level"]
    assert sensor["state"] is None
    assert sensor["allowed_commands"] == []


def test_legal_transition_updates_row(provisioned: list[dict]) -> None:
    pump_id = find(provisioned, "water_pump")["id"]

    response = transition(pump_id, "running")

    assert response.status_code == 200
    assert response.json()["state"] == "running"
    assert response.json()["allowed_commands"] == ["stop_pump"]

    stored = current(pump_id)

    assert stored["state"] == "running"
    assert stored["allowed_commands"] == ["stop_pump"]


def test_illegal_transition_does_not_update_row(provisioned: list[dict]) -> None:
    light_id = find(provisioned, "grow_light")["id"]

    assert transition(light_id, "running").status_code == 200

    response = transition(light_id, "maintenance")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Cannot move actuator from running to maintenance."
    )
    assert current(light_id)["state"] == "running"


def test_unknown_target_returns_400(provisioned: list[dict]) -> None:
    light_id = find(provisioned, "grow_light")["id"]
    before = current(light_id)["state"]

    response = transition(light_id, "flying")

    assert response.status_code == 400
    assert current(light_id)["state"] == before


def test_transition_missing_device_returns_404() -> None:
    response = transition(str(uuid4()), "running")

    assert response.status_code == 404
    assert response.json()["detail"] == "Actuator not found."


def test_transition_sensor_returns_404(provisioned: list[dict]) -> None:
    sensor_id = find(provisioned, "moisture_sensor")["id"]

    response = transition(sensor_id, "running")

    assert response.status_code == 404


def test_zone_device_list_shows_actuator_state(provisioned: list[dict]) -> None:
    config = client.post(
        "/api/locations/config",
        json={
            "location_name": f"State Site {uuid4()}",
            "zones": [{"name": "Bench 1", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.4}],
        },
    ).json()
    location_id = config["location"]["id"]
    zone_id = config["zones"][0]["id"]
    pump_id = find(provisioned, "water_pump")["id"]

    client.patch(f"/api/devices/{pump_id}/zone", json={"zone_id": zone_id})
    listed = client.get(f"/api/locations/{location_id}/zones/{zone_id}/devices").json()

    assert [d["id"] for d in listed] == [pump_id]
    assert listed[0]["state"] is not None
    assert listed[0]["allowed_commands"] == current(pump_id)["allowed_commands"]