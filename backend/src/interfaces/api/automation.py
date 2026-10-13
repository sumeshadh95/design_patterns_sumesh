from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.automation.dto import (
    RecommendationDto,
    SaveStrategyRequest,
    StrategyDto,
)
from application.automation.service import (
    AutomationService,
    LocationNotFoundError,
)
from domain.automation.strategy import UnknownStrategyError
from infrastructure.db import get_db


router = APIRouter(
    prefix="/api/locations",
    tags=["automation"],
)


@router.put(
    "/{location_id}/automation",
    response_model=StrategyDto,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Unknown strategy key"},
        404: {"description": "Location not found"},
    },
)
def save_automation(
    location_id: UUID,
    payload: SaveStrategyRequest,
    db: Session = Depends(get_db),
):
    service = AutomationService(db)

    try:
        return service.set_strategy(
            location_id,
            payload.strategy_key,
        )
    except UnknownStrategyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{location_id}/automation/evaluate",
    response_model=RecommendationDto,
    responses={
        404: {"description": "Location not found"},
    },
)
def evaluate_automation(
    location_id: UUID,
    db: Session = Depends(get_db),
):
    service = AutomationService(db)

    try:
        return service.evaluate(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
