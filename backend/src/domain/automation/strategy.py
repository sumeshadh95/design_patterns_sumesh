from __future__ import annotations

from abc import ABC, abstractmethod

from domain.automation.context import (
    LocationAutomationContext,
    Recommendation,
)


class UnknownStrategyError(ValueError):
    pass


class AutomationStrategy(ABC):
    key: str

    @abstractmethod
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        ...


class ConservativeMoistureStrategy(AutomationStrategy):
    key = "conservative"

    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        if context.moisture is None:
            return Recommendation(
                action="wait",
                reason="No moisture reading yet",
            )

        if context.moisture < context.low:
            return Recommendation(
                action="irrigate",
                reason=(
                    f"Moisture {context.moisture:.2f} "
                    f"below low {context.low:.2f}"
                ),
                score=0.9,
            )

        return Recommendation(
            action="wait",
            reason=(
                f"Moisture {context.moisture:.2f} is within "
                f"{context.low:.2f}-{context.high:.2f}"
            ),
            score=0.1,
        )


class AggressiveMoistureStrategy(AutomationStrategy):
    key = "aggressive"

    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        if context.moisture is None:
            return Recommendation(
                action="wait",
                reason="No moisture reading yet",
            )

        if context.moisture < context.high:
            return Recommendation(
                action="irrigate",
                reason=(
                    f"Moisture {context.moisture:.2f} "
                    f"below high {context.high:.2f} "
                    "(aggressive)"
                ),
                score=0.8,
            )

        return Recommendation(
            action="wait",
            reason=(
                f"Moisture {context.moisture:.2f} "
                f"above high {context.high:.2f}"
            ),
            score=0.1,
        )


_STRATEGIES: dict[str, AutomationStrategy] = {
    "conservative": ConservativeMoistureStrategy(),
    "aggressive": AggressiveMoistureStrategy(),
}


def get_strategy(key: str) -> AutomationStrategy:
    try:
        return _STRATEGIES[key]
    except KeyError:
        raise UnknownStrategyError(
            f"Unknown strategy: {key}"
        ) from None