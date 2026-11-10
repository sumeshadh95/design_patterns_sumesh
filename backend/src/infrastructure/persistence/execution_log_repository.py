from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import ActuatorExecutionLogRow


class ExecutionLogRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None,
    ) -> None:
        self._session.add(
            ActuatorExecutionLogRow(
                device_id=device_id,
                success=success,
                policy_applied=policy_applied,
                message=message,
            )
        )
        self._session.commit()

    def list_recent(self, limit: int = 20) -> list[ActuatorExecutionLogRow]:
        return list(
            self._session.execute(
                select(ActuatorExecutionLogRow)
                .order_by(ActuatorExecutionLogRow.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
