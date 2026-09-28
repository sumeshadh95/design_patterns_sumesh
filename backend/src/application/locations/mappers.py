from __future__ import annotations

from application.locations.dto import LocationConfigDto, LocationDto, ZoneDto
from infrastructure.persistence.models import LocationRow, ZoneRow


def location_config_to_dto(
    location: LocationRow,
    zones: list[ZoneRow],
) -> LocationConfigDto:
    return LocationConfigDto(
        location=LocationDto(id=location.id, name=location.name),
        zones=[
            ZoneDto(
                id=zone.id,
                location_id=zone.location_id,
                name=zone.name,
                moisture_threshold_low=float(zone.moisture_threshold_low),
                moisture_threshold_high=float(zone.moisture_threshold_high),
                schedule=zone.schedule,
            )
            for zone in zones
        ],
    )