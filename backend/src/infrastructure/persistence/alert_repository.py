from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import AlertRow


class AlertRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(
        self,
        location_id: UUID | None,
        zone_id: UUID | None,
        device_id: UUID | None,
        severity: str,
        message: str,
        event_type: str,
    ) -> AlertRow:
        row = AlertRow(
            location_id=location_id,
            zone_id=zone_id,
            device_id=device_id,
            severity=severity,
            message=message,
            event_type=event_type,
            status="active",
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)

        return row

    def list_alerts(
        self,
        status: str | None = "active",
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AlertRow]:
        stmt = select(AlertRow)

        # status=None means all statuses.
        if status is not None:
            stmt = stmt.where(AlertRow.status == status)

        if location_id is not None:
            stmt = stmt.where(AlertRow.location_id == location_id)

        if zone_id is not None:
            stmt = stmt.where(AlertRow.zone_id == zone_id)

        if since is not None:
            stmt = stmt.where(AlertRow.created_at >= since)

        return list(
            self._session.execute(
                stmt.order_by(AlertRow.created_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
