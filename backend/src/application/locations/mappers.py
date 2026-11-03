from __future__ import annotations

from application.locations.dto import LocationConfigDto, LocationDto, ZoneDto
from infrastructure.persistence.models import LocationRow, ZoneRow


def location_to_dto(location: LocationRow) -> LocationDto:
    return LocationDto(id=location.id, name=location.name)


def zone_to_dto(zone: ZoneRow) -> ZoneDto:
    return ZoneDto(
        id=zone.id,
        location_id=zone.location_id,
        name=zone.name,
        moisture_threshold_low=float(zone.moisture_threshold_low),
        moisture_threshold_high=float(zone.moisture_threshold_high),
        schedule=zone.schedule,
    )


def location_config_to_dto(
    location: LocationRow,
    zones: list[ZoneRow],
) -> LocationConfigDto:
    return LocationConfigDto(
        location=location_to_dto(location),
        zones=[zone_to_dto(zone) for zone in zones],
    )
