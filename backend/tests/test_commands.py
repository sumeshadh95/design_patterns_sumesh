from uuid import UUID, uuid4

import pytest

from domain.actuators.ports import ActuatorPort
from domain.commands.base import UnknownCommandError
from domain.commands.invoker import CommandInvoker, command_for
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import StartPumpCommand, StopPumpCommand


class SpyPort(ActuatorPort):
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, str, dict]] = []

    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        self.calls.append((device_id, command, payload))


@pytest.mark.parametrize(
    ("command_type", "command_class", "target_state"),
    [
        ("start_pump", StartPumpCommand, "running"),
        ("stop_pump", StopPumpCommand, "idle"),
        ("set_light_level", SetLightLevelCommand, "running"),
    ],
)
def test_registry_maps_type_to_command(
    command_type: str,
    command_class: type,
    target_state: str,
) -> None:
    command = command_for(command_type, uuid4(), {})

    assert isinstance(command, command_class)
    assert command.target_state == target_state


def test_unknown_command_type_raises() -> None:
    with pytest.raises(UnknownCommandError):
        command_for("open_window", uuid4(), {})


def test_invoker_executes_command_through_port() -> None:
    port = SpyPort()
    device_id = uuid4()

    CommandInvoker().run(
        command_for("set_light_level", device_id, {"level": 1}),
        port,
    )

    assert port.calls == [(device_id, "set_light_level", {"level": 1})]
