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


class OverviewDeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: str
    display_name: str


class ReadingSummaryDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime
    tracking_enabled: bool
    sampling_interval_seconds: int


class OverviewZoneDto(BaseModel):
    id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    devices: list[OverviewDeviceDto]
    latest_readings: list[ReadingSummaryDto]


class RecommendationSummaryDto(BaseModel):
    action: str
    reason: str


class LocationOverviewDto(BaseModel):
    location: LocationSummaryDto
    device_counts: DeviceCountsDto
    zones: list[OverviewZoneDto]
    strategy_key: str | None
    last_recommendation: RecommendationSummaryDto | None
