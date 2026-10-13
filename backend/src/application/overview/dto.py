from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LocationSummaryDto(BaseModel):
    id: UUID
    name: str


class DeviceCountsDto(BaseModel):
    sensor: int = 0
    actuator: int = 0


class ReadingSummaryDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime


class RecommendationSummaryDto(BaseModel):
    action: str
    reason: str


class LocationOverviewDto(BaseModel):
    location: LocationSummaryDto
    device_counts: DeviceCountsDto
    latest_readings: list[ReadingSummaryDto]
    strategy_key: str | None
    last_recommendation: RecommendationSummaryDto | None
