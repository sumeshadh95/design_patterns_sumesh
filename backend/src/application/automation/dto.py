from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SaveStrategyRequest(BaseModel):
    strategy_key: str


class StrategyDto(BaseModel):
    location_id: UUID
    strategy_key: str


class RecommendationDto(BaseModel):
    location_id: UUID
    strategy_key: str
    action: str
    reason: str
