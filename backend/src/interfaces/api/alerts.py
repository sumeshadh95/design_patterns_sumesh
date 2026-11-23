from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.alerts.dto import AlertDto
from application.alerts.service import AlertService, InvalidAlertStatusError
from infrastructure.db import get_db
from infrastructure.persistence.alert_repository import AlertRepository

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=list[AlertDto],
    responses={400: {"description": "status is not active, resolved or all"}},
)
def list_alerts(
    alert_status: str = Query(
        default="active",
        alias="status",
        description="active, resolved or all",
    ),
    location_id: UUID | None = Query(default=None),
    zone_id: UUID | None = Query(default=None),
    since: datetime | None = Query(
        default=None,
        description="Only alerts created at or after this time",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    try:
        return AlertService(AlertRepository(db)).list_alerts(
            status=alert_status,
            location_id=location_id,
            zone_id=zone_id,
            since=since,
            limit=limit,
        )
    except InvalidAlertStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
