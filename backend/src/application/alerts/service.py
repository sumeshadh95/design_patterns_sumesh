from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.alerts.dto import AlertDto
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.models import AlertRow

ALERT_STATUSES = ("active", "resolved", "all")


class InvalidAlertStatusError(ValueError):
    pass


def alert_to_dto(row: AlertRow) -> AlertDto:
    return AlertDto(
        id=row.id,
        location_id=row.location_id,
        zone_id=row.zone_id,
        device_id=row.device_id,
        severity=row.severity,
        message=row.message,
        event_type=row.event_type,
        status=row.status,
        created_at=row.created_at,
    )


class AlertService:
    def __init__(self, repository: AlertRepository):
        self._repository = repository

    def list_alerts(
        self,
        status: str = "active",
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AlertDto]:
        if status not in ALERT_STATUSES:
            raise InvalidAlertStatusError(
                "status must be active, resolved or all."
            )

        rows = self._repository.list_alerts(
            status=None if status == "all" else status,
            location_id=location_id,
            zone_id=zone_id,
            since=since,
            limit=limit,
        )

        return [alert_to_dto(row) for row in rows]
