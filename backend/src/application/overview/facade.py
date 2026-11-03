from __future__ import annotations

from collections import Counter
from uuid import UUID

from sqlalchemy.orm import Session

from application.automation.service import (
    AutomationService,
    LocationNotFoundError,
)
from application.overview.dto import (
    DeviceCountsDto,
    LocationOverviewDto,
    LocationSummaryDto,
    OverviewDeviceDto,
    OverviewZoneDto,
    ReadingSummaryDto,
    RecommendationSummaryDto,
)
from domain.devices.entity import Device
from domain.sensors.reading import Reading
from infrastructure.persistence.automation_repository import (
    AutomationRuleRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import ZoneRow
from infrastructure.persistence.overview_repository import OverviewRepository


class LocationOverviewFacade:
    def __init__(
        self,
        overview_repository: OverviewRepository,
        device_repository: DeviceRepository,
        rule_repository: AutomationRuleRepository,
        automation_service: AutomationService,
    ):
        self._overview = overview_repository
        self._devices = device_repository
        self._rules = rule_repository
        self._automation = automation_service

    @classmethod
    def from_session(cls, session: Session) -> LocationOverviewFacade:
        return cls(
            overview_repository=OverviewRepository(session),
            device_repository=DeviceRepository(session),
            rule_repository=AutomationRuleRepository(session),
            automation_service=AutomationService(session),
        )

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        location = self._overview.get_location(location_id)
        if location is None:
            raise LocationNotFoundError("Location not found.")

        zones = self._overview.list_zones(location_id)
        # Assigned devices only: this location_id and a non-null zone_id.
        devices = self._devices.list_assigned_in_location(location_id)
        readings = self._overview.latest_readings_for(
            [device.id for device in devices if device.id is not None]
        )
        counts = Counter(device.role for device in devices)

        strategy_key = self._rules.get_strategy_key(location_id)
        last_recommendation = None
        if strategy_key is not None:
            # Delegate to the Strategy subsystem; the facade never decides.
            result = self._automation.evaluate(location_id)
            last_recommendation = RecommendationSummaryDto(
                action=result.action,
                reason=result.reason,
            )

        return LocationOverviewDto(
            location=LocationSummaryDto(id=location.id, name=location.name),
            device_counts=DeviceCountsDto(
                sensor=counts.get("sensor", 0),
                actuator=counts.get("actuator", 0),
            ),
            zones=[self._zone_dto(zone, devices, readings) for zone in zones],
            strategy_key=strategy_key,
            last_recommendation=last_recommendation,
        )

    @staticmethod
    def _zone_dto(
        zone: ZoneRow,
        devices: list[Device],
        readings: dict[UUID, Reading],
    ) -> OverviewZoneDto:
        in_zone = [device for device in devices if device.zone_id == zone.id]

        return OverviewZoneDto(
            id=zone.id,
            name=zone.name,
            moisture_threshold_low=float(zone.moisture_threshold_low),
            moisture_threshold_high=float(zone.moisture_threshold_high),
            devices=[
                OverviewDeviceDto(
                    id=device.id,
                    device_type=device.device_type,
                    role=device.role,
                    display_name=device.display_name,
                )
                for device in in_zone
            ],
            latest_readings=[
                ReadingSummaryDto(
                    device_id=device.id,
                    value=readings[device.id].value,
                    unit=readings[device.id].unit,
                    recorded_at=readings[device.id].recorded_at,
                    tracking_enabled=device.tracking_enabled,
                    sampling_interval_seconds=device.sampling_interval_seconds,
                )
                for device in in_zone
                if device.id in readings
            ],
        )
