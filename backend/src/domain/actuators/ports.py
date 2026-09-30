from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class ActuatorPort(ABC):
    @abstractmethod
    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError