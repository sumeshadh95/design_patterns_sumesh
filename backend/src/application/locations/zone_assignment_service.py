from __future__ import annotations

from uuid import UUID

from domain.devices.entity import Device
from domain.locations.errors import (
    DeviceNotFoundError,
    LocationNotFoundError,
    ZoneNotFoundError,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository


class ZoneAssignmentService:
    """Places a saved device in a saved zone. Never calls the builder."""

    def __init__(
        self,
        device_repository: DeviceRepository,
        location_repository: LocationRepository,
    ):
        self._devices = device_repository
        self._locations = location_repository

    def assign(self, device_id: UUID, zone_id: UUID | None) -> Device:
        if self._devices.get_device(device_id) is None:
            raise DeviceNotFoundError("Device not found.")

        if zone_id is None:
            location_id = None
        else:
            zone = self._locations.get_zone(zone_id)
            if zone is None:
                raise ZoneNotFoundError("Zone not found.")
            # location_id always comes from the zone, never from the client.
            location_id = zone.location_id

        device = self._devices.set_zone(device_id, zone_id, location_id)
        if device is None:
            raise DeviceNotFoundError("Device not found.")

        return device

    def list_devices(self, location_id: UUID, zone_id: UUID) -> list[Device]:
        if self._locations.get_location(location_id) is None:
            raise LocationNotFoundError("Location not found.")

        zone = self._locations.get_zone(zone_id)
        if zone is None or zone.location_id != location_id:
            raise ZoneNotFoundError("Zone not found in this location.")

        return self._devices.list_in_zone(zone_id)
