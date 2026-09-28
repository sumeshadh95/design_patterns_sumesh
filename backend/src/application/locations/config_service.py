from __future__ import annotations

from uuid import UUID

from application.locations.dto import (
    BuildLocationConfigRequestDto,
    LocationConfigDto,
)
from application.locations.mappers import location_config_to_dto
from domain.locations.config_builder import LocationConfigBuilder
from infrastructure.persistence.location_repository import LocationRepository


class LocationConfigService:
    def __init__(self, repository: LocationRepository):
        self._repository = repository

    def build_and_save(
        self,
        request: BuildLocationConfigRequestDto,
    ) -> LocationConfigDto:
        builder = LocationConfigBuilder().with_location_name(request.location_name)

        for zone in request.zones:
            builder.add_zone(
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=zone.schedule,
            )

        config = builder.build()
        location, zones = self._repository.save_config(config)
        return location_config_to_dto(location, zones)

    def get_config(self, location_id: UUID) -> LocationConfigDto | None:
        result = self._repository.get_config(location_id)

        if result is None:
            return None

        location, zones = result
        return location_config_to_dto(location, zones)