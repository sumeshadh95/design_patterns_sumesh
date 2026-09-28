from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Zone:
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, Any]
    id: UUID | None = None


@dataclass(frozen=True)
class Location:
    name: str
    zones: tuple[Zone, ...]
    id: UUID | None = None


@dataclass(frozen=True)
class LocationConfig:
    location: Location