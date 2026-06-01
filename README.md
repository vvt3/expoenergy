# Exponent Energy Bus Scheduler

A Streamlit app that schedules electric bus charging along a fixed route, deciding which stations each bus uses and in what order buses share chargers.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501`.

## Project structure

```
app.py                      # Streamlit UI
core/
  scheduler.py              # Scheduling engine
  objectives.py             # Scoring framework — individual, operator, overall
  models.py                 # Bus, ChargeEvent, BusSchedule dataclasses
  route.py                  # Route topology, station config, physical constants
utils/
  loader.py                 # CSV + config loading
  time.py                   # HH:MM ↔ minutes conversion
data/
  scenario1.csv             # Even spacing
  scenario2.csv             # Bunched start
  scenario3.csv             # Asymmetric load
  scenario4.csv             # Operator heavy (KPN dominates)
  scenario5.csv             # Worst case convergence
  scenario_config.json      # Per-scenario names and weights
```

## How to change a weight

Open `data/scenario_config.json` and edit the value for the scenario you want:

```json
"scenario4": {
  "weights": {
    "individual": 1.0,
    "operator": 2.0,   // ← change this
    "overall": 1.0
  }
}
```

You can also adjust weights live using the sliders in the UI sidebar — no restart needed.

## How to add a new rule

1. Open `core/objectives.py`
2. Subclass `Objective` and implement `score(ctx: PlanContext) -> float`:

```python
class PriorityBusObjective(Objective):
    name = "priority"

    def score(self, ctx: PlanContext) -> float:
        # Priority buses never wait — penalise any wait heavily
        if ctx.bus_id.startswith("priority"):
            return -(ctx.estimated_wait * 1000)
        return 0
```

3. Register it in `DEFAULT_OBJECTIVES` at the bottom of the same file:

```python
DEFAULT_OBJECTIVES = [
    IndividualObjective(),
    OperatorObjective(),
    OverallObjective(),
    PriorityBusObjective(),   # ← add here
]
```

4. Optionally add a weight in `scenario_config.json` (defaults to `1.0`):

```json
"weights": {
  "individual": 1.0,
  "operator": 1.0,
  "overall": 1.0,
  "priority": 3.0
}
```

The scheduler engine, UI, and all existing objectives are untouched.

## How to add a new scenario

1. Create `data/scenarioN.csv` with columns: `bus_id, operator, source, destination, departure`
2. Add an entry to `data/scenario_config.json`:

```json
"scenario6": {
  "name": "My New Scenario",
  "weights": {
    "individual": 1.0,
    "operator": 1.0,
    "overall": 1.0
  }
}
```

3. Add `"scenario6"` to the dropdown list in `app.py`

## How to change the route

All route topology lives in `core/route.py`:

```python
# Add or change segments
SEGMENTS = [
    ("bengaluru", "A", 100),
    ("A", "B", 120),
    ...
]

# Add chargers to a station or add a new station
STATIONS = {
    "A": 1,
    "B": 2,   # now has 2 chargers
    "C": 1,
    "D": 1,
}

# Physical constants
MAX_RANGE = 240    # km
CHARGE_TIME = 25   # minutes
SPEED = 60         # km/h
```
