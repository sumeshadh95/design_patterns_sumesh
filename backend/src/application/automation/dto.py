from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class SaveStrategyRequest(BaseModel):
    strategy_key: str


class StrategyDto(BaseModel):
    location_id: UUID
    strategy_key: str


class ZoneRecommendationDto(BaseModel):
    zone_id: UUID
    zone_name: str
    action: str
    reason: str


class RecommendationDto(BaseModel):
    location_id: UUID
    strategy_key: str
    action: str
    reason: str
    zones: list[ZoneRecommendationDto] = Field(default_factory=list)
