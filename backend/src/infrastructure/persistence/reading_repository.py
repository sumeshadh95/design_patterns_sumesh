from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain.sensors.reading import Reading
from infrastructure.persistence.models import ReadingRow


class ReadingRepository:
    def __init__(self, session: Session):
        self._session = session

    def insert(self, reading: Reading) -> Reading:
        row = ReadingRow(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)

        return self._row_to_reading(row)

    def list_for_device(
        self,
        device_id: UUID,
        limit: int = 20,
    ) -> list[Reading]:
        rows = (
            self._session.execute(
                select(ReadingRow)
                .where(ReadingRow.device_id == device_id)
                .order_by(ReadingRow.recorded_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        return [self._row_to_reading(row) for row in rows]

    def latest_recorded_at(self, device_ids: list[UUID]) -> dict[UUID, datetime]:
        if not device_ids:
            return {}

        # One grouped query for every device, not one query per device.
        rows = self._session.execute(
            select(ReadingRow.device_id, func.max(ReadingRow.recorded_at))
            .where(ReadingRow.device_id.in_(device_ids))
            .group_by(ReadingRow.device_id)
        ).all()

        return {device_id: recorded_at for device_id, recorded_at in rows}

    @staticmethod
    def _row_to_reading(row: ReadingRow) -> Reading:
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )