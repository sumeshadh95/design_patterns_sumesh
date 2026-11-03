from __future__ import annotations

import random
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading

# Documented generation ranges for simulated values.
MOISTURE_RANGE_VWC = (0.2, 0.6)
LIGHT_RANGE_LUX = (200.0, 2000.0)


class SimulationSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("Cannot read an unpersisted device.")

        if device.device_type == "moisture_sensor":
            value = round(random.uniform(*MOISTURE_RANGE_VWC), 3)
            unit = "vwc"
        elif device.device_type == "light_sensor":
            value = round(random.uniform(*LIGHT_RANGE_LUX), 1)
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
