from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import (
    AutomationRuleRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


class AutomationRuleRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_location(self, location_id: UUID) -> AutomationRuleRow | None:
        return (
            self._session.query(AutomationRuleRow)
            .filter(AutomationRuleRow.location_id == location_id)
            .first()
        )

    def get_strategy_key(self, location_id: UUID) -> str | None:
        row = self.get_by_location(location_id)

        return row.strategy_key if row is not None else None

    def upsert_key(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> AutomationRuleRow:
        row = self.get_by_location(location_id)

        if row is None:
            row = AutomationRuleRow(
                location_id=location_id,
                strategy_key=strategy_key,
            )
            self._session.add(row)
        else:
            row.strategy_key = strategy_key
            row.updated_at = datetime.now(timezone.utc)

        self._session.commit()
        self._session.refresh(row)

        return row


class AutomationContextRepository:
    def __init__(self, session: Session):
        self._session = session

    def location_exists(self, location_id: UUID) -> bool:
        return self._session.get(LocationRow, location_id) is not None

    def zone_thresholds(
        self,
        location_id: UUID,
    ) -> tuple[float, float] | None:
        zone = (
            self._session.execute(
                select(ZoneRow)
                .where(ZoneRow.location_id == location_id)
                .order_by(ZoneRow.name)
                .limit(1)
            )
            .scalars()
            .first()
        )

        if zone is None:
            return None

        return (
            float(zone.moisture_threshold_low),
            float(zone.moisture_threshold_high),
        )

    def latest_value(self, unit: str) -> float | None:
        row = (
            self._session.execute(
                select(ReadingRow)
                .where(ReadingRow.unit == unit)
                .order_by(ReadingRow.recorded_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        return float(row.value) if row is not None else None
