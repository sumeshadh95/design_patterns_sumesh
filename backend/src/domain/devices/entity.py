from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

DEFAULT_SAMPLING_INTERVAL_SECONDS = 300
MIN_SAMPLING_INTERVAL_SECONDS = 5


@dataclass(frozen=True)
class Device:
    id: UUID | None
    device_type: str
    role: str
    device_family: str
    display_name: str
    default_config: dict[str, Any]
    zone_id: UUID | None = None
    location_id: UUID | None = None
    sampling_interval_seconds: int = DEFAULT_SAMPLING_INTERVAL_SECONDS
    tracking_enabled: bool = True

    @property
    def protocol(self) -> str:
        return str(self.default_config.get("protocol", ""))
