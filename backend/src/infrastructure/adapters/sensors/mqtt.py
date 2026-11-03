from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from domain.devices.entity import Device
from domain.sensors.reading import Reading


class MqttSensorAdapter:
    """Translates an inbound MQTT payload into a Reading.

    No broker connection here: Phase 12 delivers the payload dict, and this
    class only translates it.
    """

    def translate(self, device: Device, payload: dict[str, Any]) -> Reading:
        if device.id is None:
            raise ValueError("Cannot translate a reading for an unpersisted device.")

        try:
            value = float(payload["value"])
            unit = str(payload["unit"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "MQTT payload needs a numeric 'value' and a 'unit'."
            ) from exc

        recorded_at = payload.get("recorded_at")

        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source="mqtt",
            recorded_at=(
                datetime.fromisoformat(recorded_at)
                if recorded_at
                else datetime.now(timezone.utc)
            ),
        )
