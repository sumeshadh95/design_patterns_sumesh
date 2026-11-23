import importlib
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Self
from uuid import uuid4

import pytest

from application.alerts.subscribers import MoistureThresholdSubscriber
from domain.events.bus import EventBus
from domain.events.events import ReadingCreated, ThresholdCrossed


class FakeSession:
    """Stands in for a DB session: every zone has the given low threshold."""

    def __init__(self, low: float) -> None:
        self._low = low

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def get(self, _model: type, _key: object) -> SimpleNamespace:
        return SimpleNamespace(moisture_threshold_low=self._low)


def reading(value: float, unit: str = "vwc", zone_id=None) -> ReadingCreated:
    return ReadingCreated(
        device_id=uuid4(),
        value=value,
        unit=unit,
        source="simulation",
        recorded_at=datetime.now(UTC),
        location_id=uuid4() if zone_id else None,
        zone_id=zone_id,
    )


def test_handlers_run_in_subscription_order_for_their_event_class() -> None:
    bus = EventBus()
    calls: list[str] = []
    bus.subscribe(ReadingCreated, lambda _e: calls.append("first"))
    bus.subscribe(ReadingCreated, lambda _e: calls.append("second"))
    bus.subscribe(ThresholdCrossed, lambda _e: calls.append("other"))

    bus.publish(reading(0.3))

    assert calls == ["first", "second"]


def test_failing_handler_does_not_stop_later_handlers() -> None:
    bus = EventBus()
    calls: list[str] = []

    def broken(_event: object) -> None:
        raise RuntimeError("alert writer down")

    bus.subscribe(ReadingCreated, broken)
    bus.subscribe(ReadingCreated, lambda _e: calls.append("metrics"))

    bus.publish(reading(0.3))

    assert calls == ["metrics"]


@pytest.mark.parametrize(
    ("value", "unit", "has_zone", "expected"),
    [
        (0.10, "vwc", True, 1),   # strictly below low 0.20
        (0.20, "vwc", True, 0),   # equal to low is not below
        (0.10, "lux", True, 0),   # not a moisture reading
        (0.10, "vwc", False, 0),  # unassigned device: no zone, no threshold
    ],
)
def test_moisture_threshold_rule(
    value: float, unit: str, has_zone: bool, expected: int
) -> None:
    bus = EventBus()
    crossed: list[ThresholdCrossed] = []
    bus.subscribe(ThresholdCrossed, crossed.append)
    subscriber = MoistureThresholdSubscriber(bus, lambda: FakeSession(0.20))

    subscriber.on_reading(reading(value, unit, uuid4() if has_zone else None))

    assert len(crossed) == expected


@pytest.mark.parametrize(
    "module_name",
    [
        "application.readings.service",          # ReadingIngest
        "application.commands.service",          # CommandService
        "application.devices.actuator_state_service",  # transition service
    ],
)
def test_publishers_do_not_import_alert_repository(module_name: str) -> None:
    module = importlib.import_module(module_name)
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "AlertRepository" not in source
    assert "alert_repository" not in source
