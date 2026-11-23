from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

Handler = Callable[[Any], None]


class EventBus:
    """In-process publish/subscribe. Publishers never know the subscribers."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = {}

    def subscribe(self, event_type: type, handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: object) -> None:
        # Handlers for one event class run in subscription order. A failing
        # handler is logged and does not stop the handlers after it.
        for handler in list(self._handlers.get(type(event), [])):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler failed for %s", type(event).__name__
                )
