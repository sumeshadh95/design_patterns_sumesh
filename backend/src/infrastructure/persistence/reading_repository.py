from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
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

    @staticmethod
    def _row_to_reading(row: ReadingRow) -> Reading:
        return Reading(
            device_id=row.device_id,
            value=float(row.value),
            unit=row.unit,
            source=row.source,
            recorded_at=row.recorded_at,
        )