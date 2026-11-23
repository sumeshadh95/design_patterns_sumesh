from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AlertDto(BaseModel):
    # acknowledged_at is stored but is not part of this response.
    id: UUID
    location_id: UUID | None
    zone_id: UUID | None
    device_id: UUID | None
    severity: str
    message: str
    event_type: str
    status: str
    created_at: datetime
