from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from domain.sensors.reading import Reading
from infrastructure.persistence.models import DeviceRow, LocationRow, ReadingRow


class OverviewRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_location_name(self, location_id: UUID) -> str | None:
        row = self._session.get(LocationRow, location_id)

        return row.name if row is not None else None

    def count_devices_by_role(self) -> dict[str, int]:
        rows = self._session.execute(
            select(DeviceRow.role, func.count(DeviceRow.id)).group_by(
                DeviceRow.role
            )
        ).all()

        return {role: count for role, count in rows}

    def latest_readings(self, limit: int = 10) -> list[Reading]:
        # One query for every sensor: DISTINCT ON keeps the newest row per
        # device, so there is no query per device (no N+1).
        latest_per_device = (
            select(ReadingRow)
            .distinct(ReadingRow.device_id)
            .order_by(ReadingRow.device_id, ReadingRow.recorded_at.desc())
            .subquery()
        )
        latest = aliased(ReadingRow, latest_per_device)

        rows = (
            self._session.execute(
                select(latest)
                .order_by(latest.recorded_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return [
            Reading(
                device_id=row.device_id,
                value=float(row.value),
                unit=row.unit,
                source=row.source,
                recorded_at=row.recorded_at,
            )
            for row in rows
        ]
