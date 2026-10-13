from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from application.automation.dto import RecommendationDto
from application.automation.service import (
    AutomationService,
    LocationNotFoundError,
)
from application.overview.dto import (
    DeviceCountsDto,
    LocationOverviewDto,
    LocationSummaryDto,
    ReadingSummaryDto,
    RecommendationSummaryDto,
)
from infrastructure.persistence.automation_repository import (
    AutomationRuleRepository,
)
from infrastructure.persistence.overview_repository import OverviewRepository

LATEST_READINGS_LIMIT = 10


class LocationOverviewFacade:
    def __init__(
        self,
        overview_repository: OverviewRepository,
        rule_repository: AutomationRuleRepository,
        automation_service: AutomationService,
    ):
        self._overview = overview_repository
        self._rules = rule_repository
        self._automation = automation_service

    @classmethod
    def from_session(cls, session: Session) -> "LocationOverviewFacade":
        return cls(
            overview_repository=OverviewRepository(session),
            rule_repository=AutomationRuleRepository(session),
            automation_service=AutomationService(session),
        )

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        location_name = self._overview.get_location_name(location_id)
        if location_name is None:
            raise LocationNotFoundError("Location not found.")

        counts = self._overview.count_devices_by_role()
        readings = self._overview.latest_readings(LATEST_READINGS_LIMIT)
        recommendation = self._evaluate(location_id)

        if recommendation is not None:
            strategy_key = recommendation.strategy_key
        else:
            strategy_key = self._rules.get_strategy_key(location_id)

        return LocationOverviewDto(
            location=LocationSummaryDto(id=location_id, name=location_name),
            device_counts=DeviceCountsDto(
                sensor=counts.get("sensor", 0),
                actuator=counts.get("actuator", 0),
            ),
            latest_readings=[
                ReadingSummaryDto(
                    device_id=reading.device_id,
                    value=reading.value,
                    unit=reading.unit,
                    recorded_at=reading.recorded_at,
                )
                for reading in readings
            ],
            strategy_key=strategy_key,
            last_recommendation=(
                RecommendationSummaryDto(
                    action=recommendation.action,
                    reason=recommendation.reason,
                )
                if recommendation is not None
                else None
            ),
        )

    def _evaluate(self, location_id: UUID) -> RecommendationDto | None:
        # The decision itself belongs to the Strategy subsystem; the facade
        # only delegates. The location is already known to exist here, so the
        # only not-found case left is a location without zones.
        try:
            return self._automation.evaluate(location_id)
        except LocationNotFoundError:
            return None
