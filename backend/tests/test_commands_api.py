from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from infrastructure.db import SessionLocal
from infrastructure.persistence.models import ActuatorStateRow
from main import app

client = TestClient(app)


@pytest.fixture()
def actuators() -> dict[str, str]:
    devices = client.post("/api/devices/provision?family=simulation").json()

    return {d["device_type"]: d["id"] for d in devices if d["role"] == "actuator"}


def send(device_id: str, command_type: str, payload: dict | None = None):
    return client.post(
        "/api/commands",
        json={
            "command_type": command_type,
            "device_id": device_id,
            "payload": payload or {},
        },
    )


def saved_state(device_id: str) -> tuple[str, datetime]:
    with SessionLocal() as session:
        row = session.get(ActuatorStateRow, UUID(device_id))

        return row.state, row.updated_at


def history_for(device_id: str) -> list[dict]:
    response = client.get("/api/commands?limit=200")

    assert response.status_code == 200

    return [row for row in response.json() if row["device_id"] == device_id]


def executions_for(device_id: str) -> list[dict]:
    response = client.get("/api/actuators/executions?limit=100")

    return [row for row in response.json() if row["device_id"] == device_id]


def test_start_pump_transitions_to_running(actuators: dict[str, str]) -> None:
    pump = actuators["water_pump"]

    response = send(pump, "start_pump")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["error_message"] is None
    assert saved_state(pump)[0] == "running"
    assert history_for(pump)[0]["status"] == "success"


def test_illegal_command_rejected_logged(actuators: dict[str, str]) -> None:
    pump = actuators["water_pump"]
    before = saved_state(pump)

    # stop_pump is not in allowed_commands while the pump is idle.
    response = send(pump, "stop_pump")

    assert response.status_code == 409
    assert response.json()["status"] == "rejected"
    assert response.json()["command_type"] == "stop_pump"
    assert saved_state(pump) == before
    assert history_for(pump)[0]["status"] == "rejected"
    # The decorated port was never reached.
    assert executions_for(pump) == []


def test_max_run_time_failure_is_logged_as_failed(
    actuators: dict[str, str],
) -> None:
    pump = actuators["water_pump"]
    assert send(pump, "start_pump").status_code == 200

    with SessionLocal() as session:
        row = session.get(ActuatorStateRow, UUID(pump))
        row.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
        session.commit()

    before = saved_state(pump)
    response = send(pump, "stop_pump")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Max run time exceeded"
    assert saved_state(pump) == before
    assert executions_for(pump)[0]["success"] is False


def test_set_light_level_on_running_light_keeps_state(
    actuators: dict[str, str],
) -> None:
    light = actuators["grow_light"]

    first = send(light, "set_light_level", {"level": 1})
    assert first.status_code == 200
    assert first.json()["payload"] == {"level": 1}
    running = saved_state(light)
    assert running[0] == "running"

    second = send(light, "set_light_level", {"level": 3})

    assert second.status_code == 200
    assert second.json()["status"] == "success"
    # Already running: no transition, so updated_at did not move.
    assert saved_state(light) == running


def test_unknown_command_type_returns_400_without_row(
    actuators: dict[str, str],
) -> None:
    pump = actuators["water_pump"]

    assert send(pump, "open_window").status_code == 400
    assert history_for(pump) == []


def test_missing_or_sensor_device_returns_404() -> None:
    sensor_id = client.post("/api/sensors", json={"type": "moisture"}).json()["id"]

    assert send(str(uuid4()), "start_pump").status_code == 404
    assert send(sensor_id, "start_pump").status_code == 404
    assert history_for(sensor_id) == []


def test_history_is_newest_first_and_limited(actuators: dict[str, str]) -> None:
    pump = actuators["water_pump"]
    send(pump, "start_pump")
    send(pump, "stop_pump")

    assert [row["command_type"] for row in history_for(pump)] == [
        "stop_pump",
        "start_pump",
    ]

    response = client.get("/api/commands?limit=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert set(response.json()[0]) == {
        "id",
        "command_type",
        "device_id",
        "payload",
        "status",
        "error_message",
        "created_at",
    }
    assert client.get("/api/commands?limit=0").status_code == 422
    assert client.get("/api/commands?limit=201").status_code == 422
