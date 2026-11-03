# Phase 6 — Strategy questions

**Pattern / focus:** Strategy.

**Read first:** [Guide 06](../../materials/guides/06-strategy.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Strategy in plain language. How does the **context** use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?

> [!NOTE]
> ***Your Answer***
>
> The Strategy pattern puts different algorithms behind the same interface so they can be exchanged without changing the main application flow.
>
> In this greenhouse application, `AutomationService` is the context. It loads the saved `strategy_key`, builds a `LocationAutomationContext` (location ID, latest sensor readings, and zone moisture thresholds), and passes it to the selected strategy through:
>
> ```python
> decide(context)
> ```
>
> The strategy then returns an irrigation recommendation.
>
> Choosing the strategy and running the strategy should be separate responsibilities. The application service selects the strategy using the saved `strategy_key`, while the selected strategy performs only its own decision logic.
>
> This separation means a new strategy can be added without modifying the API route or the service.

2. Name the participants (**strategy**, **concrete strategies**, **context**, **client**). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

> [!NOTE]
> ***Your Answer***
>
> The Strategy participants in this application are:
>
> - **Strategy:** `AutomationStrategy`, which defines the common `decide(context)` method.
> - **Concrete strategies:** `ConservativeMoistureStrategy` and `AggressiveMoistureStrategy`.
> - **Context:** `AutomationService`, which picks the strategy from the saved key and delegates the decision to it. `LocationAutomationContext` is the plain input object (readings plus zone thresholds) that it passes to `decide()`.
> - **Client:** the API route and the dashboard panel, which choose and save the `strategy_key`.
>
> If all policies are placed inside one context class or API router using `if/elif`, that class becomes a conditional hotspot.
>
> For example:
>
> ```python
> if strategy_key == "conservative":
>     ...
> elif strategy_key == "aggressive":
>     ...
> ```
>
> This causes several problems:
>
> - Adding a new strategy requires modifying the same class.
> - The router becomes responsible for business algorithms.
> - Database, HTTP, and policy logic become mixed together.
> - Testing becomes more difficult.
> - Existing strategies can accidentally be affected by new changes.
> - The code does not properly use polymorphism.
>
> Each strategy should contain its own algorithm and implement the same interface.

3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a **lifecycle mode** rather than a chosen policy)?

> [!NOTE]
> ***Your Answer***
>
> Strategy should be used when several algorithms solve the same problem and the active algorithm may change based on:
>
> - configuration
> - location
> - operator choice
> - persisted policy
> - runtime conditions
>
> In this application, conservative and aggressive irrigation policies are suitable Strategy implementations because both decide whether irrigation should be recommended.
>
> Strategy should be skipped when:
>
> - there is only one algorithm
> - the algorithm is very small
> - there is no realistic possibility of another policy
> - creating separate strategy classes would add unnecessary complexity
>
> A simple function is clearer when only one fixed algorithm exists.
>
> Strategy should also be avoided when the variation represents the lifecycle of an object rather than a selected policy. For example, a pump being `idle`, `running`, or `faulted` is better represented by the State pattern.

## B. This phase of the application

4. In this lab, what does a strategy’s `decide(context)` return (action + reason)? Give a concrete difference you implemented (or were required to implement) between **conservative** and **aggressive** on the **same** moisture reading and zone thresholds.

> [!NOTE]
> ***Your Answer***
>
> The `decide(context)` method returns a `Recommendation`.
>
> The recommendation contains:
>
> - `action`
> - `reason`
> - optional `score`
>
> The action can be:
>
> ```text
> irrigate
> ```
>
> or:
>
> ```text
> wait
> ```
>
> Example context:
>
> ```text
> moisture = 0.40
> low threshold = 0.25
> high threshold = 0.45
> ```
>
> The conservative strategy checks the low threshold:
>
> ```text
> 0.40 is not below 0.25
> ```
>
> Therefore it returns:
>
> ```text
> action: wait
> reason: Moisture 0.40 is within 0.25-0.45
> ```
>
> The aggressive strategy checks the high threshold:
>
> ```text
> 0.40 is below 0.45
> ```
>
> Therefore it returns:
>
> ```text
> action: irrigate
> reason: Moisture 0.40 below high 0.45 (aggressive)
> ```
>
> Both strategies receive the same context, but they produce different recommendations because they use different policies. They disagree for every moisture value inside the band `low <= moisture < high`.

5. Where do the numbers in `LocationAutomationContext` (or your equivalent) come from? Latest moisture may already be in `sensor_readings` from a manual read, the simulation sampler, or MQTT translation — why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from **zones**, not hardcoded in the strategy class?

> [!NOTE]
> ***Your Answer***
>
> The values come from the database, and the service builds **one context per zone**:
>
> - `location_id` comes from the request path, and `zone_id`, `low` and `high` come from that zone's row (`zones.moisture_threshold_low` and `zones.moisture_threshold_high`).
> - `moisture` is the newest `vwc` reading among sensors whose `devices.zone_id` is that zone, and `light` is the newest `lux` reading from the same zone.
> - A zone with no assigned moisture sensor gets no moisture value. Both strategies then return `wait` with the reason "No moisture sensor reading in this zone". A reading from an unassigned device is never borrowed.
>
> The newest row may come from a manual read, the simulation sampler or an MQTT translation. The strategy only reads the newest stored row and does not care how it arrived. Adding a scheduler or a broker here would mix collecting data with deciding on it; Phase 5 already owns the sampler, and Phase 12 owns the transports.
>
> Strategies receive a plain context object because the domain should not depend on SQLAlchemy, FastAPI, HTTP requests, database sessions or Pydantic schemas. That keeps them independent, reusable and easy to unit test.
>
> The thresholds come from `zones` because they are configuration. Each zone can have its own moisture band, and the operator can edit it on the dashboard. Hardcoding values in a strategy would ignore that configuration.

6. The active `strategy_key` is **persisted** per `location_id` (for example in `automation_rules`). Why must `POST .../automation/evaluate` use the **saved** key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

> [!NOTE]
> ***Your Answer***
>
> The active strategy represents the operator's selected configuration for that location.
>
> The `PUT` endpoint saves the selected key in:
>
> ```text
> automation_rules
> ```
>
> The evaluate endpoint then loads the saved key from the database. If a location has no saved rule yet, the service falls back to `conservative`.
>
> This is important because evaluation should use the actual configured policy, not a temporary value supplied only for one request.
>
> If the client sends a strategy key only during evaluation:
>
> - the result may not match the saved configuration
> - the decision becomes difficult to audit
> - different clients may evaluate different policies
> - the dashboard and backend can become inconsistent
>
> When the operator changes the saved strategy from conservative to aggressive, the next evaluation uses aggressive behaviour even if the moisture reading remains unchanged.
>
> For example:
>
> ```text
> moisture = 0.40
> low = 0.25
> high = 0.45
> ```
>
> Before changing the saved key:
>
> ```text
> conservative -> wait
> ```
>
> After changing the saved key:
>
> ```text
> aggressive -> irrigate
> ```
>
> The input data is the same, but the selected algorithm has changed.

7. Strategy **recommends** (irrigate / wait). It should not itself start a pump. Why keep **decide** separate from **execute**? Which later pattern is meant to carry out the action?

> [!NOTE]
> ***Your Answer***
>
> A Strategy should decide what should happen. It should not directly control hardware.
>
> The Strategy returns a recommendation such as:
>
> ```text
> irrigate
> ```
>
> or:
>
> ```text
> wait
> ```
>
> It should not immediately call the pump actuator because decision-making and execution are separate responsibilities.
>
> Keeping them separate provides several advantages:
>
> - strategies can be unit tested without hardware
> - recommendations can be logged
> - an operator can review or approve a recommendation
> - safety checks can run before execution
> - commands can be queued or retried
> - the strategy remains independent from actuator implementations
>
> The later **Command pattern** (Phase 10) is intended to represent and execute actions such as starting irrigation.

## C. Compare, contrast, and scenarios

8. Contrast Strategy with **State** (Phase 8). Both delegate to an object with the same shape. Who typically **changes** the active object, and is the variation a **policy** or a **lifecycle**?

> [!NOTE]
> ***Your Answer***
>
> Strategy and State both delegate behaviour to another object, but they solve different problems.
>
> **Strategy** represents a replaceable policy or algorithm.
>
> In this application:
>
> ```text
> ConservativeMoistureStrategy
> AggressiveMoistureStrategy
> ```
>
> The operator, configuration, or application service typically selects or changes the active strategy.
>
> **State** represents the lifecycle condition of an object.
>
> For example, a pump might have these states:
>
> ```text
> Idle
> Running
> Completed
> Faulted
> ```
>
> The object or its state machine typically changes the active state as events occur.
>
> The difference is:
>
> ```text
> Strategy = policy variation
> State = lifecycle variation
> ```
>
> The greenhouse operator may change the irrigation strategy. The pump changes state because of events such as starting, completing, or failing.

9. Contrast Strategy with **Adapter** (Phase 5) and with **Builder** (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

> [!NOTE]
> ***Your Answer***
>
> The three patterns have different purposes:
>
> **Strategy**
> Strategy swaps an algorithm or policy.
>
> In Phase 06:
>
> ```text
> ConservativeMoistureStrategy
> AggressiveMoistureStrategy
> ```
>
> Both implement the same decision interface but use different irrigation rules.
>
> **Adapter**
> Adapter translates an incompatible external interface into the interface expected by the application.
>
> In Phase 05, a sensor adapter converts simulation or vendor-specific sensor data into a normalized reading used by the application.
>
> ```text
> vendor or simulation data -> normalized Reading
> ```
>
> **Builder**
> Builder assembles a valid complex object or aggregate step by step.
>
> In Phase 04, the Builder creates a valid location configuration containing zones, moisture thresholds, and schedules.
>
> Therefore:
>
> ```text
> Adapter  -> translates a foreign API
> Builder  -> assembles a valid aggregate
> Strategy -> swaps an algorithm
> ```

10. A classmate writes one “mega-strategy” that still contains `if conservative` / `if aggressive` inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> A mega-strategy that contains:
>
> ```python
> if conservative:
>     ...
> elif aggressive:
>     ...
> ```
>
> has not properly separated the algorithms. It still keeps all policy logic in one class.
>
> This causes:
>
> - one conditional hotspot
> - difficult maintenance
> - more complicated testing
> - increased risk when adding new strategies
> - violation of the purpose of Strategy
>
> Instead, the algorithms should be separated:
>
> ```python
> class ConservativeMoistureStrategy(AutomationStrategy):
>     ...
>
> class AggressiveMoistureStrategy(AutomationStrategy):
>     ...
> ```
>
> The application should select the correct object through a registry or lookup function such as `get_strategy(key)`.
>
> A strategy that immediately calls the actuator adapter is also a trap. It mixes the decision policy with physical execution.
>
> For example, the strategy should not do this:
>
> ```python
> pump.start()
> ```
>
> The strategy should only return:
>
> ```text
> action = irrigate
> ```
>
> The application can later pass that recommendation to a Command or actuator execution component.
>
> Separating decision from execution makes the system easier to:
>
> - test
> - log
> - review
> - approve
> - queue
> - retry
> - protect with safety checks
>
> The Strategy recommends the action. The later Command or execution layer performs the action.
