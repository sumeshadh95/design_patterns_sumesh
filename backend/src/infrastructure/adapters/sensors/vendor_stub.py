from __future__ import annotations

import random
from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class VendorStubSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("Cannot read an unpersisted device.")

        raw_payload = self._read_vendor_payload(device)

        if raw_payload["kind"] == "soil_probe":
            value = raw_payload["measurement"]["fraction"]
            unit = "vwc"
        elif raw_payload["kind"] == "lux_meter":
            value = raw_payload["measurement"]["illuminance"]
            unit = "lux"
        else:
            raise ValueError("Vendor returned an unsupported sensor payload.")

        return Reading(
            device_id=device.id,
            value=float(value),
            unit=unit,
            source="vendor",
            recorded_at=datetime.fromisoformat(raw_payload["captured_at"]),
        )

    @staticmethod
    def _read_vendor_payload(device: Device) -> dict:
        captured_at = datetime.now(timezone.utc).isoformat()

        if device.device_type == "moisture_sensor":
            return {
                "kind": "soil_probe",
                "measurement": {"fraction": round(random.uniform(0.25, 0.45), 3)},
                "captured_at": captured_at,
            }

        if device.device_type == "light_sensor":
            return {
                "kind": "lux_meter",
                "measurement": {"illuminance": round(random.uniform(300.0, 800.0), 1)},
                "captured_at": captured_at,
            }

        raise ValueError(f"Unsupported vendor sensor type: {device.device_type}")