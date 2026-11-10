# Course phase documentation

This directory contains notes and answers for the Smart Greenhouse course phases.

## Phase order

1. **Phase 1 — Skeleton:** runnable three-tier foundation.
2. **Phase 2 — Factory Method:** devices, sensor creators, and the Sensors dashboard section.
3. **Phase 3 — Abstract Factory:** simulation and edge device families.
4. **Phase 4 — Builder:** location configuration, location list and delete, zone add/edit/delete, and device-to-zone assignment.
5. **Phase 5 — Adapter:** sensor ports and adapters (simulation, vendor stub, MQTT translator), one ingest path, and the simulation sampler.
6. **Phase 6 — Strategy:** pluggable irrigation policies saved per location and evaluated per zone.
7. **Phase 7 — Facade:** one overview endpoint and dashboard section per location, grouped by zone.
8. **Phase 8 — State:** persisted actuator lifecycle with guarded transitions.
9. **Phase 9 — Decorator:** logging and max run-time decorators around the actuator port, with a persisted execution log.

10. **Phase 10 — Command**
11. **Phase 11 — Observer**
12. **Phase 12 — Production API, WebSocket, and schema hardening**

## Completed phase documentation

- [Phase 1 — Skeleton answers](phase-01/questions.md)
- [Phase 2 — Factory Method answers](phase-02/questions.md)
- [Factory Method pattern note](../patterns/factory-method.md)
- [Phase 3 — Abstract Factory answers](phase-03/questions.md)
- [Abstract Factory pattern note](../patterns/abstract-factory.md)
- [Phase 4 — Builder answers](phase-04/questions.md)
- [Builder pattern note](../patterns/builder.md)
- [Phase 5 — Adapter answers](phase-05/questions.md)
- [Adapter pattern note](../patterns/adapter.md)
- [Phase 6 — Strategy answers](phase-06/questions.md)
- [Strategy pattern note](../patterns/strategy.md)
- [Phase 7 — Facade answers](phase-07/questions.md)
- [Facade pattern note](../patterns/facade.md)
- [Phase 8 — State answers](phase-08/questions.md)
- [State pattern note](../patterns/state.md)
- [Phase 9 — Decorator answers](phase-09/questions.md)
- [Decorator pattern note](../patterns/decorator.md)


## Migration chain

| Revision | Phase | Adds |
| --- | --- | --- |
| `001` | 1 | baseline |
| `d6e3a525172c` | 2 | `devices` (with `role`) |
| `5479eeddebbe` | 3 | `devices.device_family` |
| `f828466f474c` | 4 | `locations`, `zones` |
| `ca9bdac13be8` | 5 | `sensor_readings` (`571c1412ac65` is an empty follow-up) |
| `0cf1c6efdcaa` | 6 | `automation_rules` |
| `b676258b7285` | 8 | `actuator_states` |
| `c3a1d5e7f902` | 4 (update) | `devices.zone_id`, `devices.location_id` |
| `d8b2e6f4a113` | 5 (update) | `devices.sampling_interval_seconds`, `devices.tracking_enabled`, protocol values |
| `aed8dbcb6b7c` | 9 | `actuator_execution_log` |


The last two revisions add the updated Phase 4 and Phase 5 requirements. They come after `b676258b7285` because applied revisions are never edited.
