from __future__ import annotations

from sqlalchemy import select
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

    def get_config(
        self,
        location_id,
    ) -> tuple[LocationRow, list[ZoneRow]] | None:
        location = self._session.get(LocationRow, location_id)

        if location is None:
            return None

        zones = (
            self._session.execute(
                select(ZoneRow)
                .where(ZoneRow.location_id == location_id)
                .order_by(ZoneRow.name)
            )
            .scalars()
            .all()
        )

        return location, zones