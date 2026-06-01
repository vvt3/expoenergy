# Architecture

## Scheduling approach

The scheduler uses a **greedy simulation with scored plan selection**. For each bus (processed in departure order), it enumerates every physically valid charging plan, scores each one against a set of weighted objectives, and commits the best plan before moving to the next bus.

This is not globally optimal — it does not backtrack or consider how a choice for bus N affects bus N+5. That tradeoff was intentional. A greedy approach is:

- Fast enough to rerun on every UI interaction (weight slider change rerenders instantly)
- Deterministic and explainable — you can trace exactly why a bus got a given plan
- Easy to extend — the scoring step is fully pluggable

A globally optimal approach (e.g. constraint programming, integer linear programming) would produce better schedules under extreme contention but would require a solver dependency, be much harder to extend with new rules, and be overkill for the current scale. The greedy approach scales linearly with bus count and plan count.

---

## How plan selection works

For each bus, the scheduler:

1. Builds the route path from source to destination
2. Generates all valid charging plans — combinations of intermediate stations where no gap between consecutive charges exceeds the battery range (240 km)
3. Simulates the bus travelling under each plan, tracking wait times and charger state
4. Scores each plan using the objective framework (see below)
5. Commits the highest-scoring plan, updating shared charger state for subsequent buses

A key correctness detail: charger state is snapshotted before simulation so the congestion penalty reads pre-existing queues, not ones created by the bus being evaluated. Without this, 3-stop plans always appear more congested than 2-stop plans because they touch more stations.

---

## Objective framework

Soft rules live in `core/objectives.py` as independent classes. Each objective implements one method:

```python
class Objective:
    name: str
    def score(self, ctx: PlanContext) -> float:
        ...  # return a negative number: more negative = worse
```

`PlanContext` is a dataclass passed to every objective containing everything it could need: this bus's wait times, journey duration, stop count, operator fleet state, and pre-existing station backlogs.

The scheduler sums weighted scores:

```
total = Σ weights[objective.name] * objective.score(ctx)
```

Weights come from `scenario_config.json` and are exposed as sliders in the UI. If a weight key is missing it defaults to `1.0`, so new objectives don't break existing scenario configs.

The three current objectives:

**IndividualObjective** (`"individual"`) — penalises this bus's own wait time and journey duration. Only stops where the bus actually queued are penalised; stops where the charger was free are not.

**OperatorObjective** (`"operator"`) — penalises plans that add to an operator's cumulative fleet wait. When one operator has many buses (scenario 4 — 8 KPN buses), this steers later buses toward less contested plans to keep the fleet moving smoothly.

**OverallObjective** (`"overall"`) — penalises choosing stations that already have a long queue backlog. This distributes load across stations naturally: if B is heavily queued, buses are pushed toward A or C even if B would otherwise be the direct choice.

---

## Data structure design

### `scenario_config.json`

Each scenario is a keyed object with a human-readable name and a weights dict. The weights dict is open-ended — any new objective just needs a matching key.

```json
{
  "scenario4": {
    "name": "Operator Heavy",
    "weights": {
      "individual": 1.0,
      "operator": 2.0,
      "overall": 1.0
    }
  }
}
```

### Scenario CSV

Each row is one bus. Fields: `bus_id`, `operator`, `source`, `destination`, `departure`.

`source` and `destination` are plain city names. The route is derived at runtime from `route.py` — the CSV does not encode the path, which means adding a new intermediate city or extending the route requires no changes to any scenario file.

### `route.py`

Route topology lives here as data, not scattered through logic:

- `SEGMENTS` — list of `(start, end, distance_km)` tuples
- `STATIONS` — dict of `station_name: charger_count`
- `MAX_RANGE`, `CHARGE_TIME`, `SPEED` — physical constants

---

## Anticipated future changes and how the design handles them

**Adding a new soft rule (e.g. time-of-day electricity cost, priority buses, driver shift limits)**
Create a subclass of `Objective`, implement `score(ctx)`, add it to `DEFAULT_OBJECTIVES`. Add its weight key to scenario configs. No changes to the scheduler engine, router, or UI.

**Changing a weight**
Edit the value in `scenario_config.json` for the relevant scenario, or drag the slider in the UI. One place, no code changes.

**Adding a new charging station**
Add a row to `SEGMENTS` and an entry to `STATIONS` in `route.py`. No CSV changes, no scheduler changes. The path builder and plan generator derive everything from `SEGMENTS` at runtime.

**Adding a second charger to a station**
Change the value in `STATIONS`: `"B": 2`. The scheduler already tracks a list of charger free-times per station and always assigns the earliest available one. No logic changes.

**Adding a new operator**
Add buses to the CSV with the new operator name. `OperatorObjective` reads operator names dynamically from `operator_wait_time` — no hardcoded operator list anywhere.

**Adding a new route (e.g. Bengaluru → Mumbai)**
Add the new segments to `SEGMENTS`. Add buses with the new source/destination pair to a scenario CSV. `build_path` constructs the path from the segment graph at runtime.

**Adding a new scenario**
Add a CSV to `data/` and a config entry to `scenario_config.json`. Add the key to the dropdown in `app.py`. Three files, no logic changes.

**Scaling to more buses**
The greedy algorithm is O(buses × plans × path_length). Plan count grows combinatorially with station count but is bounded by `MAX_RANGE` — most combinations are invalid and filtered early. For the current route (4 stations, 8 valid plans) this is negligible. For a much larger network a plan cache keyed on `(source, destination)` would avoid regenerating plans for every bus.

**Multiple routes sharing stations**
`station_free_time` is already keyed by station name, not by route. Buses from different routes competing for the same charger would work correctly today with no changes — the scheduler resolves contention by charger availability regardless of which route a bus is on.

**Adding hard constraints (e.g. a station is closed, a bus has a curfew)**
Hard constraints belong in `generate_valid_plans` (filter out plans that violate them) or as a `-inf` return in a new `Objective.score` implementation. Either way they're isolated from existing logic.

---

## Assumptions made

- Buses travel at a fixed uniform speed (60 km/h). Travel time equals distance in minutes at this speed, so 100 km = 100 minutes. The spec states "all buses travel at the same speed" and gives no traffic or variation.
- Charging always fills to full (240 km range). Partial charges are not modelled.
- Buses are processed in departure order. A bus that departs earlier gets first access to chargers, which is a fair real-world proxy.
- Bengaluru and Kochi are not scheduling stations. Buses depart with a full charge from both endpoints as stated in the spec.
- If two plans score identically the first one encountered wins. Ties are rare given floating-point scoring.
- `scenario_config.json` is the single source of truth for weights. The UI sliders override these at runtime but do not write back to the file.
