from __future__ import annotations

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command


class SetLightLevelCommand(Command):
    command_type = "set_light_level"
    # An idle light starts running; an already running light stays running.
    target_state = "running"

    def execute(self, port: ActuatorPort) -> None:
        port.apply(self.device_id, self.command_type, self.payload)
