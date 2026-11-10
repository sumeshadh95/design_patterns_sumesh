from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from infrastructure.db import SessionLocal
from infrastructure.persistence.models import ActuatorStateRow
from main import app

client = TestClient(app)


@pytest.fixture()
def pump_id() -> str:
    devices = client.post("/api/devices/provision?family=simulation").json()

    return next(d["id"] for d in devices if d["device_type"] == "water_pump")


def apply(device_id: str, command: str):
    return client.post(
        f"/api/actuators/{device_id}/apply",
        json={"command": command, "payload": {}},
    )


def executions_for(device_id: str) -> list[dict]:
    response = client.get("/api/actuators/executions?limit=100")

    assert response.status_code == 200

    return [row for row in response.json() if row["device_id"] == device_id]


def test_apply_writes_successful_execution_row(pump_id: str) -> None:
    response = apply(pump_id, "start_pump")

    assert response.status_code == 204

    rows = executions_for(pump_id)

    assert len(rows) == 1
    assert rows[0]["success"] is True
    assert rows[0]["policy_applied"] == ["logging"]
    assert rows[0]["message"] is None



def test_blocked_attempt_is_logged_as_unsuccessful(pump_id: str) -> None:
    assert client.post(
        f"/api/devices/{pump_id}/transition",
        json={"target": "running"},
    ).status_code == 200

    # Force a running state older than the max run time.
    with SessionLocal() as session:
        row = session.get(ActuatorStateRow, UUID(pump_id))
        row.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
        session.commit()

    response = apply(pump_id, "stop_pump")

    assert response.status_code == 409
    assert response.json()["detail"] == "Max run time exceeded"

    newest = executions_for(pump_id)[0]

    assert newest["success"] is False
    assert newest["policy_applied"] == ["maxRunTime", "logging"]
    assert newest["message"] == "Max run time exceeded"


def test_executions_are_newest_first_and_limited(pump_id: str) -> None:
    apply(pump_id, "start_pump")
    apply(pump_id, "start_pump")

    times = [row["created_at"] for row in executions_for(pump_id)]

    assert len(times) == 2
    assert times == sorted(times, reverse=True)

    response = client.get("/api/actuators/executions?limit=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert set(response.json()[0]) == {
        "id",
        "device_id",
        "success",
        "policy_applied",
        "message",
        "created_at",
    }


def test_apply_to_missing_or_sensor_device_returns_404() -> None:
    sensor_id = client.post("/api/sensors", json={"type": "moisture"}).json()["id"]

    assert apply(str(uuid4()), "start_pump").status_code == 404
    assert apply(sensor_id, "start_pump").status_code == 404
    assert executions_for(sensor_id) == []
