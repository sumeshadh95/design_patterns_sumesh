from __future__ import annotations

from uuid import UUID

from application.locations.dto import ZoneDto, ZoneUpsertRequestDto
from application.locations.mappers import zone_to_dto
from domain.locations.config_builder import validate_zone_fields
from domain.locations.errors import (
    ConfigurationError,
    LocationNotFoundError,
    ZoneNotFoundError,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.models import ZoneRow


class ZoneService:
    """Add, edit and delete zones on a saved location without the builder."""

    def __init__(
        self,
        location_repository: LocationRepository,
        device_repository: DeviceRepository,
    ):
        self._locations = location_repository
        self._devices = device_repository

    def add_zone(self, location_id: UUID, request: ZoneUpsertRequestDto) -> ZoneDto:
        if self._locations.get_location(location_id) is None:
            raise LocationNotFoundError("Location not found.")

        name = self._validated_name(location_id, request)
        zone = self._locations.add_zone(
            location_id,
            name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
            request.schedule,
        )

        return zone_to_dto(zone)

    def update_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
        request: ZoneUpsertRequestDto,
    ) -> ZoneDto:
        zone = self._get_zone(location_id, zone_id)
        name = self._validated_name(location_id, request, exclude_zone_id=zone.id)
        updated = self._locations.update_zone(
            zone,
            name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
            request.schedule,
        )

        return zone_to_dto(updated)

    def delete_zone(self, location_id: UUID, zone_id: UUID) -> None:
        zone = self._get_zone(location_id, zone_id)

        if self._locations.count_zones(location_id) <= 1:
            raise ConfigurationError(
                "A location must keep at least one zone; this is the last zone."
            )

        # ON DELETE SET NULL would clear zone_id only, so both columns are
        # cleared here, in the same transaction as the zone delete.
        self._devices.clear_zone_assignments(zone.id)
        self._locations.delete_zone(zone)

    def _get_zone(self, location_id: UUID, zone_id: UUID) -> ZoneRow:
        if self._locations.get_location(location_id) is None:
            raise LocationNotFoundError("Location not found.")

        zone = self._locations.get_zone(zone_id)
        if zone is None or zone.location_id != location_id:
            raise ZoneNotFoundError("Zone not found in this location.")

        return zone

    def _validated_name(
        self,
        location_id: UUID,
        request: ZoneUpsertRequestDto,
        exclude_zone_id: UUID | None = None,
    ) -> str:
        validate_zone_fields(
            request.name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
        )
        name = request.name.strip()

        if self._locations.zone_name_taken(location_id, name, exclude_zone_id):
            raise ConfigurationError("Zone names must be unique within a location.")

        return name
