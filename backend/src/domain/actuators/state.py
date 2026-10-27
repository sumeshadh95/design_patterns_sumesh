from __future__ import annotations

from abc import ABC
from typing import ClassVar

DEFAULT_STATE = "idle"


class UnknownStateError(ValueError):
    pass


class IllegalTransitionError(ValueError):
    pass


class ActuatorState(ABC):
    name: ClassVar[str]
    targets: ClassVar[frozenset[str]]
    commands: ClassVar[dict[str, tuple[str, ...]]] = {}

    def can_transition_to(self, target: str) -> bool:
        return target in self.targets

    def allowed_commands(self, device_type: str) -> list[str]:
        return list(self.commands.get(device_type, ()))


class OffState(ActuatorState):
    name = "off"
    targets = frozenset({"idle"})


class IdleState(ActuatorState):
    name = "idle"
    targets = frozenset({"running", "maintenance", "error", "off"})
    commands = {
        "water_pump": ("start_pump",),
        "grow_light": ("set_light_level",),
    }


class RunningState(ActuatorState):
    name = "running"
    targets = frozenset({"idle", "error"})
    commands = {
        "water_pump": ("stop_pump",),
        "grow_light": ("set_light_level",),
    }


class ErrorState(ActuatorState):
    name = "error"
    targets = frozenset({"idle", "maintenance"})


class MaintenanceState(ActuatorState):
    name = "maintenance"
    targets = frozenset({"idle"})


_STATES: dict[str, ActuatorState] = {
    state.name: state
    for state in (
        OffState(),
        IdleState(),
        RunningState(),
        ErrorState(),
        MaintenanceState(),
    )
}

STATE_NAMES: tuple[str, ...] = tuple(_STATES)


def get_state(name: str) -> ActuatorState:
    try:
        return _STATES[name]
    except KeyError:
        raise UnknownStateError(f"Unknown actuator state: {name}") from None
