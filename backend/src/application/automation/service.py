from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from application.automation.dto import (
    RecommendationDto,
    StrategyDto,
    ZoneRecommendationDto,
)
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

        # One context per zone: that zone's thresholds and the latest reading
        # from sensors assigned to that zone only.
        zone_results: list[ZoneRecommendationDto] = []
        for zone in self._context.list_zone_thresholds(location_id):
            context = LocationAutomationContext(
                location_id=location_id,
                zone_id=zone.zone_id,
                moisture=self._context.latest_value_in_zone(zone.zone_id, "vwc"),
                light=self._context.latest_value_in_zone(zone.zone_id, "lux"),
                low=zone.low,
                high=zone.high,
            )
            recommendation = strategy.decide(context)
            zone_results.append(
                ZoneRecommendationDto(
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    action=recommendation.action,
                    reason=recommendation.reason,
                )
            )

        irrigate = [zone for zone in zone_results if zone.action == "irrigate"]

        if irrigate:
            action = "irrigate"
            reason = "; ".join(f"{zone.zone_name}: {zone.reason}" for zone in irrigate)
        else:
            action = "wait"
            reason = "No zone needs water."

        return RecommendationDto(
            location_id=location_id,
            strategy_key=strategy_key,
            action=action,
            reason=reason,
            zones=zone_results,
        )
