from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class LocationAutomationContext:
    location_id: UUID
    moisture: float | None
    light: float | None
    low: float
    high: float


@dataclass(frozen=True)
class Recommendation:
    action: str
    reason: str
    score: float | None = None