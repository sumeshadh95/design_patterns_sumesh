from __future__ import annotations

from domain.actuators.state import (
    DEFAULT_STATE,
    IllegalTransitionError,
    get_state,
)


class ActuatorContext:
    def __init__(self, device_type: str, state: str = DEFAULT_STATE):
        self._device_type = device_type
        self._state = get_state(state)

    @property
    def state(self) -> str:
        return self._state.name

    def transition(self, target: str) -> None:
        next_state = get_state(target)

        if not self._state.can_transition_to(target):
            raise IllegalTransitionError(
                f"Cannot move actuator from {self._state.name} to {target}."
            )

        self._state = next_state

    def allowed_commands(self) -> list[str]:
        return self._state.allowed_commands(self._device_type)
