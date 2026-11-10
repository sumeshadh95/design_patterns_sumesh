from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from domain.actuators.ports import ActuatorPort, PolicyViolationError
from infrastructure.adapters.actuators.logging_decorator import (
    LoggingActuatorDecorator,
)
from infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
)

NOW = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
MAX_RUN_TIME = timedelta(minutes=30)


class SpyActuator(ActuatorPort):
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple[UUID, str, dict]] = []
        self._error = error

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.calls.append((device_id, command, payload))

        if self._error is not None:
            raise self._error


class FakeStates:
    def __init__(self, running_since: datetime | None) -> None:
        self._running_since = running_since

    def get_running_since(self, device_id: UUID) -> datetime | None:
        return self._running_since


class FakeLog:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> None:
        self.rows.append(
            {
                "device_id": device_id,
                "success": success,
                "policy_applied": policy_applied,
                "message": message,
            }
        )


def build_stack(running_since: datetime | None, inner: SpyActuator, log: FakeLog):
    # Same order as the composition root: logging outermost.
    max_runtime = MaxRunTimeActuatorDecorator(
        inner,
        FakeStates(running_since),
        MAX_RUN_TIME,
        clock=lambda: NOW,
    )

    return LoggingActuatorDecorator(max_runtime, log)


def test_max_runtime_does_not_call_inner() -> None:
    inner = SpyActuator()
    decorator = MaxRunTimeActuatorDecorator(
        inner,
        FakeStates(NOW - timedelta(minutes=30)),
        MAX_RUN_TIME,
        clock=lambda: NOW,
    )

    with pytest.raises(PolicyViolationError, match="Max run time exceeded"):
        decorator.apply(uuid4(), "stop_pump", {})

    assert inner.calls == []


@pytest.mark.parametrize(
    "running_since",
    [None, NOW - timedelta(minutes=5)],
    ids=["not-running", "within-limit"],
)
def test_max_runtime_allows_apply(running_since: datetime | None) -> None:
    inner = SpyActuator()
    decorator = MaxRunTimeActuatorDecorator(
        inner,
        FakeStates(running_since),
        MAX_RUN_TIME,
        clock=lambda: NOW,
    )
    device_id = uuid4()

    decorator.apply(device_id, "start_pump", {"duration": 30})

    assert inner.calls == [(device_id, "start_pump", {"duration": 30})]


def test_logging_records_successful_apply() -> None:
    inner = SpyActuator()
    log = FakeLog()
    device_id = uuid4()

    build_stack(None, inner, log).apply(device_id, "start_pump", {})

    assert len(inner.calls) == 1
    assert log.rows == [
        {
            "device_id": device_id,
            "success": True,
            "policy_applied": ["logging"],
            "message": None,

        }
    ]


def test_failed_policy_writes_execution_row() -> None:
    inner = SpyActuator()
    log = FakeLog()
    device_id = uuid4()
    stack = build_stack(NOW - timedelta(hours=1), inner, log)

    with pytest.raises(PolicyViolationError):
        stack.apply(device_id, "stop_pump", {})

    assert inner.calls == []
    assert log.rows == [
        {
            "device_id": device_id,
            "success": False,
            "policy_applied": ["maxRunTime", "logging"],
            "message": "Max run time exceeded",
        }
    ]


def test_logging_records_inner_failure() -> None:
    log = FakeLog()

    with pytest.raises(OSError):
        build_stack(None, SpyActuator(OSError("relay offline")), log).apply(
            uuid4(), "start_pump", {}
        )

    assert [row["success"] for row in log.rows] == [False]
    assert log.rows[0]["message"] == "relay offline"
