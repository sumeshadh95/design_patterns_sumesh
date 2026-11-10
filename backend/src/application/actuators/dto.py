from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ApplyCommandRequest(BaseModel):
    command: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class ExecutionDto(BaseModel):
    id: UUID
    device_id: UUID
    success: bool
    policy_applied: list[str]
    message: str | None
    created_at: datetime
