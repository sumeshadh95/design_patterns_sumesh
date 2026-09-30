from __future__ import annotations

from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class SimulationSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("Cannot read an unpersisted device.")

        if device.device_type == "moisture_sensor":
            value = 0.31
            unit = "vwc"
        elif device.device_type == "light_sensor":
            value = 420.0
            unit = "lux"
        else:
            raise ValueError(f"Unsupported sensor type: {device.device_type}")

        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        )