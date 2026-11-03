from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from application.readings.sampler import SimulationSampler
from domain.devices.entity import Device
from main import app

client = TestClient(app)

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def sensor(protocol: str = "simulation", tracking: bool = True, interval: int = 60):
    return Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Fake",
        default_config={"protocol": protocol},
        sampling_interval_seconds=interval,
        tracking_enabled=tracking,
    )


class FakeDevices:
    """Mimics the repository query: simulation protocol and tracking on."""

    def __init__(self, devices: list[Device]):
        self.devices = devices

    def list_tracked_simulation_sensors(self) -> list[Device]:
        return [
            d for d in self.devices
            if d.protocol == "simulation" and d.tracking_enabled
        ]


class FakeReadings:
    def __init__(self):
        self.last: dict[UUID, datetime] = {}

    def latest_recorded_at(self, device_ids):
        return {i: self.last[i] for i in device_ids if i in self.last}


class FakeIngest:
    def __init__(self, readings: FakeReadings):
        self.readings = readings
        self.now = T0
        self.recorded: list[UUID] = []

    def take_reading(self, device_id: UUID):
        self.recorded.append(device_id)
        self.readings.last[device_id] = self.now


def test_sampler_respects_interval_and_tracking() -> None:
    tracked = sensor(interval=60)
    disabled = sensor(tracking=False)
    mqtt = sensor(protocol="mqtt")

    readings = FakeReadings()
    ingest = FakeIngest(readings)
    sampler = SimulationSampler(FakeDevices([tracked, disabled, mqtt]), readings, ingest)

    # No previous row counts as elapsed.
    assert sampler.run_once(T0) == 1
    assert ingest.recorded == [tracked.id]

    # Inside the interval: nothing new.
    assert sampler.run_once(T0 + timedelta(seconds=30)) == 0

    # After the interval: one more row.
    ingest.now = T0 + timedelta(seconds=60)
    assert sampler.run_once(T0 + timedelta(seconds=60)) == 1

    # Disabled and MQTT devices never got a sampler row.
    assert disabled.id not in ingest.recorded
    assert mqtt.id not in ingest.recorded


def test_sampling_patch_updates_device() -> None:
    created = client.post(
        "/api/sensors",
        json={"type": "moisture", "display_name": f"Sampling {uuid4()}"},
    )
    assert created.status_code == 201
    sensor_id = created.json()["id"]
    assert created.json()["sampling_interval_seconds"] == 300
    assert created.json()["tracking_enabled"] is True

    response = client.patch(
        f"/api/devices/{sensor_id}/sampling",
        json={"sampling_interval_seconds": 30, "tracking_enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["sampling_interval_seconds"] == 30
    assert response.json()["tracking_enabled"] is False


def test_sampling_patch_rejects_short_interval() -> None:
    created = client.post("/api/sensors", json={"type": "light"})
    sensor_id = created.json()["id"]

    response = client.patch(
        f"/api/devices/{sensor_id}/sampling",
        json={"sampling_interval_seconds": 4, "tracking_enabled": True},
    )

    assert response.status_code == 400


def test_sampling_patch_missing_device_returns_404() -> None:
    response = client.patch(
        f"/api/devices/{uuid4()}/sampling",
        json={"sampling_interval_seconds": 30, "tracking_enabled": True},
    )

    assert response.status_code == 404
