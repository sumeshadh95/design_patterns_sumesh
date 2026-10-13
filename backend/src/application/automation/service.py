from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from application.automation.dto import RecommendationDto, StrategyDto
from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import get_strategy
from infrastructure.persistence.automation_repository import (
    AutomationContextRepository,
    AutomationRuleRepository,
)

DEFAULT_STRATEGY_KEY = "conservative"


class LocationNotFoundError(LookupError):
    pass


class AutomationService:
    def __init__(self, session: Session):
        self._rules = AutomationRuleRepository(session)
        self._context = AutomationContextRepository(session)

    def set_strategy(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> StrategyDto:
        get_strategy(strategy_key)

        if not self._context.location_exists(location_id):
            raise LocationNotFoundError("Location not found.")

        self._rules.upsert_key(location_id, strategy_key)

        return StrategyDto(
            location_id=location_id,
            strategy_key=strategy_key,
        )

    def evaluate(self, location_id: UUID) -> RecommendationDto:
        if not self._context.location_exists(location_id):
            raise LocationNotFoundError("Location not found.")

        strategy_key = (
            self._rules.get_strategy_key(location_id)
            or DEFAULT_STRATEGY_KEY
        )
        strategy = get_strategy(strategy_key)

        thresholds = self._context.zone_thresholds(location_id)
        if thresholds is None:
            raise LocationNotFoundError("No zones for location.")

        low, high = thresholds

        context = LocationAutomationContext(
            location_id=location_id,
            moisture=self._context.latest_value("vwc"),
            light=self._context.latest_value("lux"),
            low=low,
            high=high,
        )

        recommendation = strategy.decide(context)

        return RecommendationDto(
            location_id=location_id,
            strategy_key=strategy_key,
            action=recommendation.action,
            reason=recommendation.reason,
        )
