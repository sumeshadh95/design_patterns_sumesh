from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import ActuatorStateRow


class ActuatorStateRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_state(self, device_id: UUID) -> str | None:
        row = self._session.get(ActuatorStateRow, device_id)

        return row.state if row is not None else None

    def get_states(self, device_ids: list[UUID]) -> dict[UUID, str]:
        if not device_ids:
            return {}

        # One query for the whole device list, not one per actuator.
        rows = self._session.execute(
            select(ActuatorStateRow.device_id, ActuatorStateRow.state).where(
                ActuatorStateRow.device_id.in_(device_ids)
            )
        ).all()

        return {device_id: state for device_id, state in rows}

    def get_running_since(self, device_id: UUID) -> datetime | None:
        row = self._session.get(ActuatorStateRow, device_id)

        if row is None or row.state != "running":
            return None

        # updated_at changes on every transition, so for a running actuator
        # it is the moment it started running.
        return row.updated_at


    def save_state(self, device_id: UUID, state: str) -> None:
        row = self._session.get(ActuatorStateRow, device_id)

        if row is None:
            self._session.add(ActuatorStateRow(device_id=device_id, state=state))
        else:
            row.state = state
            row.updated_at = datetime.now(timezone.utc)

        self._session.commit()

    def ensure_states(self, device_ids: list[UUID], state: str) -> None:
        existing = self.get_states(device_ids)
        missing = [
            device_id for device_id in device_ids if device_id not in existing
        ]

        if not missing:
            return

        self._session.add_all(
            ActuatorStateRow(device_id=device_id, state=state)
            for device_id in missing
        )
        self._session.commit()
