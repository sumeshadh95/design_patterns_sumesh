from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from domain.sensors.reading import Reading
from infrastructure.persistence.models import LocationRow, ReadingRow, ZoneRow


class OverviewRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_location(self, location_id: UUID) -> LocationRow | None:
        return self._session.get(LocationRow, location_id)

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

    def latest_readings_for(self, device_ids: list[UUID]) -> dict[UUID, Reading]:
        if not device_ids:
            return {}

        # One query for all devices: DISTINCT ON keeps the newest row per
        # device, so there is no reading query per device (no N+1).
        latest_per_device = (
            select(ReadingRow)
            .where(ReadingRow.device_id.in_(device_ids))
            .distinct(ReadingRow.device_id)
            .order_by(ReadingRow.device_id, ReadingRow.recorded_at.desc())
            .subquery()
        )
        latest = aliased(ReadingRow, latest_per_device)
        rows = self._session.execute(select(latest)).scalars().all()

        return {
            row.device_id: Reading(
                device_id=row.device_id,
                value=float(row.value),
                unit=row.unit,
                source=row.source,
                recorded_at=row.recorded_at,
            )
            for row in rows
        }
