from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import CommandLogRow


class CommandLogRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(
        self,
        command_type: str,
        device_id: UUID,
        payload: dict[str, Any],
        status: str,
        error_message: str | None,
    ) -> CommandLogRow:
        row = CommandLogRow(
            command_type=command_type,
            device_id=device_id,
            payload=payload,
            status=status,
            error_message=error_message,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)

        return row

    def list_recent(self, limit: int = 50) -> list[CommandLogRow]:
        return list(
            self._session.execute(
                select(CommandLogRow)
                .order_by(CommandLogRow.created_at.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
