from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from application.alerts.subscribers import AlertPersistenceSubscriber
from application.event_bus import event_bus
from application.readings.service import ReadingIngest
from domain.events.bus import EventBus
from domain.events.events import CommandFailed, ReadingCreated
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import ActuatorStateRow
from infrastructure.persistence.reading_repository import ReadingRepository
from main import app

client = TestClient(app)


@pytest.fixture()
def site() -> dict[str, str]:
    """A location with Bench 1 and Bench 2 (low 0.20) and a fresh family."""
    config = client.post(
        "/api/locations/config",
        json={
            "location_name": f"Observer site {uuid4().hex[:6]}",
            "zones": [
                {"name": "Bench 1", "moisture_threshold_low": 0.20,
                 "moisture_threshold_high": 0.45},
                {"name": "Bench 2", "moisture_threshold_low": 0.20,
                 "moisture_threshold_high": 0.45},
            ],
        },
    ).json()
    zones = {zone["name"]: zone["id"] for zone in config["zones"]}
    devices = client.post("/api/devices/provision?family=simulation").json()
    by_type = {device["device_type"]: device["id"] for device in devices}

    return {
        "location": config["location"]["id"],
        "bench1": zones["Bench 1"],
        "bench2": zones["Bench 2"],
        "moisture": by_type["moisture_sensor"],
        "pump": by_type["water_pump"],
    }


def assign(device_id: str, zone_id: str) -> None:
    response = client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": zone_id})
    assert response.status_code == 200


def ingest_moisture(sensor_id: str, value: float, bus: EventBus = event_bus) -> None:
    """MQTT translation path: translate a payload, then the one ingest."""
    with SessionLocal() as session:
        devices = DeviceRepository(session)
        device = devices.get_device(UUID(sensor_id))
        reading = MqttSensorAdapter().translate(device, {"value": value, "unit": "vwc"})
        ReadingIngest(devices, ReadingRepository(session), bus).record(device.id, reading)


def alerts(query: str = "") -> list[dict]:
    response = client.get(f"/api/alerts?limit=200{query}")
    assert response.status_code == 200
    return response.json()


def alerts_for(device_id: str, query: str = "") -> list[dict]:
    return [row for row in alerts(query) if row["device_id"] == device_id]


def test_ingest_with_tracking_on_publishes_reading_created(site: dict[str, str]) -> None:
    assign(site["moisture"], site["bench1"])
    bus = EventBus()
    seen: list[ReadingCreated] = []
    bus.subscribe(ReadingCreated, seen.append)

    ingest_moisture(site["moisture"], 0.33, bus)

    assert len(seen) == 1
    assert seen[0].value == 0.33
    assert seen[0].unit == "vwc"
    assert seen[0].source == "mqtt"
    assert str(seen[0].zone_id) == site["bench1"]
    assert str(seen[0].location_id) == site["location"]


def test_ingest_with_tracking_off_stores_without_publishing(site: dict[str, str]) -> None:
    sensor = site["moisture"]
    assert client.patch(
        f"/api/devices/{sensor}/sampling",
        json={"sampling_interval_seconds": 300, "tracking_enabled": False},
    ).status_code == 200
    bus = EventBus()
    seen: list[ReadingCreated] = []
    bus.subscribe(ReadingCreated, seen.append)

    ingest_moisture(sensor, 0.33, bus)

    assert seen == []
    stored = client.get(f"/api/sensors/{sensor}/readings?limit=1").json()
    assert stored[0]["value"] == 0.33


def test_low_moisture_on_bench_1_inserts_threshold_alert(site: dict[str, str]) -> None:
    sensor = site["moisture"]
    assign(sensor, site["bench1"])

    ingest_moisture(sensor, 0.10)

    rows = alerts_for(sensor, f"&zone_id={site['bench1']}")
    assert len(rows) == 1
    assert rows[0]["event_type"] == "threshold.crossed"
    assert rows[0]["severity"] == "warning"
    assert rows[0]["message"] == "Moisture below zone low"
    assert rows[0]["status"] == "active"
    assert rows[0]["location_id"] == site["location"]
    assert rows[0]["zone_id"] == site["bench1"]
    assert set(rows[0]) == {
        "id", "location_id", "zone_id", "device_id", "severity",
        "message", "event_type", "status", "created_at",
    }
    # Another zone's filter does not return it; the location filter does.
    assert alerts_for(sensor, f"&zone_id={site['bench2']}") == []
    assert len(alerts_for(sensor, f"&location_id={site['location']}")) == 1


def test_post_read_on_tracked_sensor_uses_the_same_publish(site: dict[str, str]) -> None:
    sensor = site["moisture"]
    # A dry zone: every simulated value (0.2-0.6) is below low 0.95.
    dry = client.post(
        f"/api/locations/{site['location']}/zones",
        json={"name": "Dry bench", "moisture_threshold_low": 0.95,
              "moisture_threshold_high": 0.99},
    ).json()["id"]
    assign(sensor, dry)

    assert client.post(f"/api/sensors/{sensor}/read").status_code == 200
    assert len(alerts_for(sensor, f"&zone_id={dry}")) == 1

    # Tracking off: the read is stored, but nothing is published.
    client.patch(
        f"/api/devices/{sensor}/sampling",
        json={"sampling_interval_seconds": 300, "tracking_enabled": False},
    )
    assert client.post(f"/api/sensors/{sensor}/read").status_code == 200
    assert len(alerts_for(sensor, f"&zone_id={dry}")) == 1


def test_failed_command_on_unassigned_pump_has_null_ids(site: dict[str, str]) -> None:
    pump = site["pump"]
    command = {"device_id": pump, "payload": {}}
    assert client.post("/api/commands", json={**command, "command_type": "start_pump"}).status_code == 200

    with SessionLocal() as session:
        row = session.get(ActuatorStateRow, UUID(pump))
        row.updated_at = datetime.now(UTC) - timedelta(hours=1)
        session.commit()

    response = client.post("/api/commands", json={**command, "command_type": "stop_pump"})
    assert response.json()["status"] == "failed"

    rows = alerts_for(pump)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "command.failed"
    assert rows[0]["severity"] == "warning"
    assert rows[0]["message"] == "Max run time exceeded"
    assert rows[0]["location_id"] is None
    assert rows[0]["zone_id"] is None


def test_transition_to_error_inserts_critical_alert(site: dict[str, str]) -> None:
    pump = site["pump"]

    response = client.post(f"/api/devices/{pump}/transition", json={"target": "error"})
    assert response.status_code == 200

    rows = alerts_for(pump)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "state.changed"
    assert rows[0]["severity"] == "critical"
    assert rows[0]["message"] == "Actuator entered error"


def test_transition_to_other_states_inserts_no_alert(site: dict[str, str]) -> None:
    pump = site["pump"]

    assert client.post(f"/api/devices/{pump}/transition", json={"target": "running"}).status_code == 200
    assert client.post(f"/api/devices/{pump}/transition", json={"target": "idle"}).status_code == 200

    assert alerts_for(pump) == []


def test_alert_persistence_subscriber_inserts_on_published_event(
    site: dict[str, str],
) -> None:
    bus = EventBus()
    bus.subscribe(CommandFailed, AlertPersistenceSubscriber(SessionLocal).on_command)

    bus.publish(
        CommandFailed(
            device_id=UUID(site["pump"]),
            location_id=None,
            zone_id=None,
            command_type="stop_pump",
            message="Relay offline",
        )
    )

    rows = alerts_for(site["pump"])
    assert [row["message"] for row in rows] == ["Relay offline"]


def test_alert_list_filters_and_order(site: dict[str, str]) -> None:
    pump = site["pump"]
    for target in ("error", "idle", "error"):
        client.post(f"/api/devices/{pump}/transition", json={"target": target})

    rows = alerts_for(pump)
    assert len(rows) == 2
    times = [row["created_at"] for row in rows]
    assert times == sorted(times, reverse=True)

    assert alerts_for(pump, "&status=resolved") == []
    assert len(alerts_for(pump, "&status=all")) == 2
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    assert alerts_for(pump, f"&since={future}") == []

    assert client.get("/api/alerts?status=bogus").status_code == 400
    assert client.get("/api/alerts?limit=0").status_code == 422
    assert client.get("/api/alerts?limit=201").status_code == 422
    assert len(client.get("/api/alerts?limit=1").json()) <= 1
