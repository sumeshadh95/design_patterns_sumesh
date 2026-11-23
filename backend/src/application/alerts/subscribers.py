from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from domain.events.bus import EventBus
from domain.events.events import (
    ActuatorStateChanged,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.location_repository import LocationRepository

SessionFactory = Callable[[], Session]


class MoistureThresholdSubscriber:
    """reading.created -> threshold.crossed when moisture is below zone low."""

    def __init__(self, bus: EventBus, session_factory: SessionFactory) -> None:
        self._bus = bus
        self._session_factory = session_factory

    def on_reading(self, event: ReadingCreated) -> None:
        # No zone means no threshold: never invent one.
        if event.unit != "vwc" or event.zone_id is None:
            return

        with self._session_factory() as session:
            zone = LocationRepository(session).get_zone(event.zone_id)
            low = float(zone.moisture_threshold_low) if zone is not None else None

        if low is None or not event.value < low:
            return

        self._bus.publish(
            ThresholdCrossed(
                device_id=event.device_id,
                location_id=event.location_id,
                zone_id=event.zone_id,
                moisture=event.value,
                threshold_low=low,
            )
        )


class AlertPersistenceSubscriber:
    """The only writer of the alerts table."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def on_threshold(self, event: ThresholdCrossed) -> None:
        self._insert(event, "warning", "Moisture below zone low")

    def on_command(self, event: CommandFailed) -> None:
        self._insert(event, "warning", event.message)

    def on_state(self, event: ActuatorStateChanged) -> None:
        # Only the error state is an alert.
        if event.state != "error":
            return

        self._insert(event, "critical", "Actuator entered error")

    def _insert(
        self,
        event: ThresholdCrossed | CommandFailed | ActuatorStateChanged,
        severity: str,
        message: str,
    ) -> None:
        with self._session_factory() as session:
            AlertRepository(session).add(
                location_id=event.location_id,
                zone_id=event.zone_id,
                device_id=event.device_id,
                severity=severity,
                message=message,
                event_type=event.event_type,
            )
