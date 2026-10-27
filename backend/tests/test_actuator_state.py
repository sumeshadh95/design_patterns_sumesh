import pytest

from domain.actuators.context import ActuatorContext
from domain.actuators.state import (
    STATE_NAMES,
    IllegalTransitionError,
    UnknownStateError,
)

LEGAL_EDGES = {
    ("off", "idle"),
    ("idle", "running"),
    ("idle", "maintenance"),
    ("idle", "error"),
    ("idle", "off"),
    ("running", "idle"),
    ("running", "error"),
    ("error", "idle"),
    ("error", "maintenance"),
    ("maintenance", "idle"),
}

ALL_EDGES = [(source, target) for source in STATE_NAMES for target in STATE_NAMES]


def test_idle_to_running_allowed() -> None:
    context = ActuatorContext("water_pump", "idle")

    context.transition("running")

    assert context.state == "running"


def test_running_to_maintenance_rejected() -> None:
    context = ActuatorContext("water_pump", "running")

    with pytest.raises(IllegalTransitionError):
        context.transition("maintenance")

    assert context.state == "running"


@pytest.mark.parametrize(("source", "target"), ALL_EDGES)
def test_transition_table(source: str, target: str) -> None:
    context = ActuatorContext("water_pump", source)

    if (source, target) in LEGAL_EDGES:
        context.transition(target)
        assert context.state == target
    else:
        with pytest.raises(IllegalTransitionError):
            context.transition(target)
        assert context.state == source


def test_unknown_target_state_rejected() -> None:
    context = ActuatorContext("water_pump", "idle")

    with pytest.raises(UnknownStateError):
        context.transition("flying")

    assert context.state == "idle"


def test_unknown_stored_state_rejected() -> None:
    with pytest.raises(UnknownStateError):
        ActuatorContext("water_pump", "flying")


@pytest.mark.parametrize(
    ("device_type", "state", "expected"),
    [
        ("water_pump", "idle", ["start_pump"]),
        ("water_pump", "running", ["stop_pump"]),
        ("grow_light", "idle", ["set_light_level"]),
        ("grow_light", "running", ["set_light_level"]),
        ("water_pump", "off", []),
        ("water_pump", "error", []),
        ("water_pump", "maintenance", []),
    ],
)
def test_allowed_commands_follow_state(
    device_type: str,
    state: str,
    expected: list[str],
) -> None:
    assert ActuatorContext(device_type, state).allowed_commands() == expected
