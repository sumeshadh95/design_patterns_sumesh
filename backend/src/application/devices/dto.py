from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: Literal["sensor", "actuator"]
    device_family: str
    display_name: str
    default_config: dict[str, Any]
    zone_id: UUID | None = None
    location_id: UUID | None = None
    sampling_interval_seconds: int
    tracking_enabled: bool
    state: str | None = None
    allowed_commands: list[str] = Field(default_factory=list)


class TransitionRequest(BaseModel):
    target: str


class AssignZoneRequest(BaseModel):
    zone_id: UUID | None


class SamplingUpdateRequest(BaseModel):
    sampling_interval_seconds: int
    tracking_enabled: bool
