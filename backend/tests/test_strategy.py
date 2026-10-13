from uuid import uuid4

import pytest

from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import (
    UnknownStrategyError,
    get_strategy,
)


def make_context(
    moisture: float,
) -> LocationAutomationContext:
    return LocationAutomationContext(
        location_id=uuid4(),
        moisture=moisture,
        light=None,
        low=0.25,
        high=0.45,
    )


def test_conservative_waits_when_within_band():
    context = make_context(0.40)

    recommendation = get_strategy(
        "conservative",
    ).decide(context)

    assert recommendation.action == "wait"
    assert "0.40" in recommendation.reason


def test_aggressive_differs_on_same_context():
    context = make_context(0.40)

    conservative = get_strategy(
        "conservative",
    ).decide(context)

    aggressive = get_strategy(
        "aggressive",
    ).decide(context)

    assert conservative.action != aggressive.action
    assert aggressive.action == "irrigate"


def test_unknown_key_rejected():
    with pytest.raises(UnknownStrategyError):
        get_strategy("nope")