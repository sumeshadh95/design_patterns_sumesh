from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.overview.dto import LocationOverviewDto
from application.overview.facade import (
    LocationNotFoundError,
    LocationOverviewFacade,
)
from infrastructure.db import get_db

router = APIRouter(prefix="/api/locations", tags=["overview"])


def get_overview_facade(
    db: Session = Depends(get_db),
) -> LocationOverviewFacade:
    return LocationOverviewFacade.from_session(db)


@router.get(
    "/{location_id}/overview",
    response_model=LocationOverviewDto,
    responses={
        404: {"description": "Location not found"},
    },
)
def get_location_overview(
    location_id: UUID,
    facade: LocationOverviewFacade = Depends(get_overview_facade),
):
    try:
        return facade.get_overview(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
