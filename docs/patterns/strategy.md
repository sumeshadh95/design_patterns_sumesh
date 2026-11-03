# Strategy — Automation Policies

## Problem

The greenhouse needs to support different irrigation policies.

A conservative policy can wait until moisture falls below the low
threshold. An aggressive policy can irrigate earlier when moisture falls
below the high threshold.

Putting all policies inside the API router would create a growing set of
`if` and `elif` statements. The Strategy pattern keeps the algorithms
separate and replaceable.

## Intent

Strategy defines a common interface for a family of algorithms.

The application selects an automation strategy by its persisted key.
The selected strategy receives a plain location context and returns an
irrigation recommendation.

The API chooses and persists the strategy. The strategy object only
performs the decision algorithm.

## Interface

```python
class AutomationStrategy(ABC):
    key: str

    @abstractmethod
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        ...
```

`LocationAutomationContext` is a frozen dataclass with `location_id`,
`zone_id`, `moisture`, `light`, `low` and `high`. There is one context per zone. `Recommendation` has `action`
(`irrigate` or `wait`), `reason` and an optional `score`.

`get_strategy(key)` looks the key up in a registry and raises
`UnknownStrategyError` for an unknown key, before `decide` is ever called.

## Difference between the two strategies

| Strategy | Rule |
| --- | --- |
| `conservative` | irrigate only when moisture is below the zone **low** threshold |
| `aggressive` | irrigate as soon as moisture is below the zone **high** threshold |

Same context, different recommendation:

| Moisture | Low | High | conservative | aggressive |
| --- | --- | --- | --- | --- |
| 0.40 | 0.25 | 0.45 | `wait` | `irrigate` |
| 0.20 | 0.25 | 0.45 | `irrigate` | `irrigate` |
| 0.50 | 0.25 | 0.45 | `wait` | `wait` |

The strategies disagree for every moisture value inside the band
`low <= moisture < high`. A zone with no moisture reading from its own sensors gets
`moisture = None`, and both strategies return `wait` with the reason
"No moisture sensor reading in this zone".

## Persistence choice

The active key is stored in a dedicated `automation_rules` table, not as
columns on `locations`.

| Column | Type |
| --- | --- |
| `id` | UUID primary key |
| `location_id` | UUID, foreign key to `locations`, unique |
| `strategy_key` | VARCHAR(32) |
| `parameters` | JSONB, nullable |
| `updated_at` | timestamptz |

The unique index on `location_id` guarantees one active strategy per
location. A location that has no rule yet is evaluated with the default
key `conservative`.

## Where in code

| Role | File |
| --- | --- |
| Strategy interface, concrete strategies, registry | `backend/src/domain/automation/strategy.py` |
| Context and recommendation | `backend/src/domain/automation/context.py` |
| DTOs | `backend/src/application/automation/dto.py` |
| Service that selects the strategy and calls `decide` | `backend/src/application/automation/service.py` |
| Rule and context repositories | `backend/src/infrastructure/persistence/automation_repository.py` |
| `AutomationRuleRow` | `backend/src/infrastructure/persistence/models.py` |
| API routes | `backend/src/interfaces/api/automation.py` |
| Dashboard panel | `frontend/src/features/automation/StrategyPanel.tsx` |
| Unit tests | `backend/tests/test_strategy.py` |
| API tests (per-zone evaluate) | `backend/tests/test_automation_api.py` |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| PUT | `/api/locations/{location_id}/automation` | save the strategy key |
| POST | `/api/locations/{location_id}/automation/evaluate` | evaluate with the saved key |

An unknown key returns 400. A missing location returns 404.

## How the context is built

`AutomationService.evaluate` does the following:

1. Checks that the location exists (404 otherwise).
2. Loads the persisted `strategy_key` for the location (default
   `conservative` when none is saved).
3. For **each zone** of the location, builds one `LocationAutomationContext`
   from that zone's low and high thresholds and the newest `vwc` and `lux`
   readings among sensors whose `devices.zone_id` is that zone.
4. Calls `get_strategy(key).decide(context)` once per zone.
5. Returns `{ location_id, strategy_key, action, reason }` plus a `zones`
   list with each zone's own action and reason. The top-level action is
   `irrigate` when any zone needs water, otherwise `wait` with the reason
   "No zone needs water."

A reading from an unassigned device, or from a sensor in another zone, is
never used. Readings may come from a manual read, the Phase 5 sampler or a
translated MQTT payload; evaluate only reads the newest stored row. This
phase adds no scheduler and no broker.

The strategies import no SQLAlchemy and never see ORM rows.
## Decide, not execute

A strategy only recommends `irrigate` or `wait`. It does not start a pump.
Executing the action belongs to the Command pattern in Phase 10.

## Exercise: add a third strategy

Add a `BalancedMoistureStrategy` that irrigates when moisture is below the
midpoint of the band.

1. Add the class in `backend/src/domain/automation/strategy.py`:

   ```python
   class BalancedMoistureStrategy(AutomationStrategy):
       key = "balanced"

       def decide(
           self,
           context: LocationAutomationContext,
       ) -> Recommendation:
           if context.moisture is None:
               return Recommendation(
                   action="wait",
                   reason="No moisture sensor reading in this zone",
               )

           midpoint = (context.low + context.high) / 2

           if context.moisture < midpoint:
               return Recommendation(
                   action="irrigate",
                   reason=(
                       f"Moisture {context.moisture:.2f} "
                       f"below midpoint {midpoint:.2f}"
                   ),
               )

           return Recommendation(
               action="wait",
               reason=(
                   f"Moisture {context.moisture:.2f} "
                   f"at or above midpoint {midpoint:.2f}"
               ),
           )
   ```

2. Register it in `_STRATEGIES` with the key `"balanced"`.
3. Add `<option value="balanced">balanced</option>` to `StrategyPanel.tsx`.
4. Add a unit test with moisture 0.30 and 0.40 for the band 0.25-0.45.

The service, the repositories and the router stay unchanged. That is the
point of the pattern.
