from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from domain.locations.entity import LocationConfig
from infrastructure.persistence.models import LocationRow, ZoneRow


class LocationRepository:
    def __init__(self, session: Session):
        self._session = session

    def save_config(
        self,
        config: LocationConfig,
    ) -> tuple[LocationRow, list[ZoneRow]]:
        try:
            location = LocationRow(name=config.location.name)
            self._session.add(location)
            self._session.flush()

            zones = [
                ZoneRow(
                    location_id=location.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=zone.schedule,
                )
                for zone in config.location.zones
            ]
            self._session.add_all(zones)
            self._session.commit()

            self._session.refresh(location)
            for zone in zones:
                self._session.refresh(zone)

            return location, zones
        except Exception:
            self._session.rollback()
            raise

    def get_location(self, location_id: UUID) -> LocationRow | None:
        return self._session.get(LocationRow, location_id)

    def get_config(
        self,
        location_id: UUID,
    ) -> tuple[LocationRow, list[ZoneRow]] | None:
        location = self.get_location(location_id)

        if location is None:
            return None

        return location, self.list_zones(location_id)

    def list_locations(self) -> list[LocationRow]:
        # Oldest first, so a new location is appended at the end of the list.
        return list(
            self._session.execute(
                select(LocationRow).order_by(LocationRow.created_at, LocationRow.id)
            )
            .scalars()
            .all()
        )

    def delete_location(self, location_id: UUID) -> bool:
        # Zones go with the location (ON DELETE CASCADE). Devices keep their
        # rows; zone_id and location_id are set to NULL by their foreign keys.
        result = self._session.execute(
            delete(LocationRow).where(LocationRow.id == location_id)
        )
        self._session.commit()

        return result.rowcount > 0

    def list_zones(self, location_id: UUID) -> list[ZoneRow]:
        return list(
            self._session.execute(
                select(ZoneRow)
                .where(ZoneRow.location_id == location_id)
                .order_by(ZoneRow.name)
            )
            .scalars()
            .all()
        )

    def get_zone(self, zone_id: UUID) -> ZoneRow | None:
        return self._session.get(ZoneRow, zone_id)

    def count_zones(self, location_id: UUID) -> int:
        return self._session.execute(
            select(func.count(ZoneRow.id)).where(ZoneRow.location_id == location_id)
        ).scalar_one()

    def zone_name_taken(
        self,
        location_id: UUID,
        name: str,
        exclude_zone_id: UUID | None = None,
    ) -> bool:
        stmt = select(ZoneRow.id).where(
            ZoneRow.location_id == location_id,
            func.lower(ZoneRow.name) == name.strip().lower(),
        )

        if exclude_zone_id is not None:
            stmt = stmt.where(ZoneRow.id != exclude_zone_id)

        return self._session.execute(stmt).first() is not None

    def add_zone(
        self,
        location_id: UUID,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict[str, Any],
    ) -> ZoneRow:
        zone = ZoneRow(
            location_id=location_id,
            name=name,
            moisture_threshold_low=moisture_threshold_low,
            moisture_threshold_high=moisture_threshold_high,
            schedule=schedule,
        )
        self._session.add(zone)
        self._session.commit()
        self._session.refresh(zone)

        return zone

    def update_zone(
        self,
        zone: ZoneRow,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict[str, Any],
    ) -> ZoneRow:
        zone.name = name
        zone.moisture_threshold_low = moisture_threshold_low
        zone.moisture_threshold_high = moisture_threshold_high
        zone.schedule = schedule
        self._session.commit()
        self._session.refresh(zone)

        return zone

    def delete_zone(self, zone: ZoneRow) -> None:
        # The caller clears device assignments first; both happen in this commit.
        self._session.delete(zone)
        self._session.commit()
