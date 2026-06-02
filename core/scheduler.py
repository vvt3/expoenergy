from core.models import BusSchedule, ChargeEvent
from core.route import build_path, generate_valid_plans, get_distance
from core.route import CHARGE_TIME, MAX_RANGE, STATIONS, SEGMENTS
from core.objectives import DEFAULT_OBJECTIVES, PlanContext


class Scheduler:
    def __init__(self, objectives=None):
        self.objectives = objectives if objectives is not None else DEFAULT_OBJECTIVES

    def schedule(self, buses, weights):
        schedules = []
        station_free_time = {
            station: [0] * chargers for station, chargers in STATIONS.items()
        }
        operator_wait_time = {}

        buses = sorted(buses, key=lambda b: b.departure)

        for bus in buses:
            path = build_path(bus.source, bus.destination)
            plans = generate_valid_plans(path)
            chosen_plan = self.choose_plan(
                bus, plans, weights, station_free_time, operator_wait_time
            )

            if chosen_plan is None:
                raise Exception(f"No valid charging plan found for {bus.bus_id}")

            events, final_arrival = self._execute_plan(
                bus, path, chosen_plan, station_free_time
            )

            total_wait = sum(e.wait_time for e in events)
            operator_wait_time.setdefault(bus.operator, 0)
            operator_wait_time[bus.operator] += total_wait

            schedules.append(
                BusSchedule(
                    bus_id=bus.bus_id,
                    source=bus.source,
                    destination=bus.destination,
                    events=events,
                    final_arrival_time=final_arrival,
                )
            )

        return schedules

    # ------------------------------------------------------------------
    # Plan selection
    # ------------------------------------------------------------------

    def choose_plan(self, bus, plans, weights, station_free_time, operator_wait_time):
        best_plan = None
        best_score = float("-inf")

        for plan in plans:
            score = self.score_plan(
                bus, plan, weights, station_free_time, operator_wait_time
            )
            if score > best_score:
                best_score = score
                best_plan = plan

        return best_plan

    def score_plan(self, bus, plan, weights, station_free_time, operator_wait_time):
        # snapshot charger state BEFORE
        original_station_times = {
            s: times.copy() for s, times in station_free_time.items()
        }
        temp_station_times = {s: times.copy() for s, times in station_free_time.items()}

        path = build_path(bus.source, bus.destination)
        sim_time = int(bus.departure)
        battery = MAX_RANGE
        estimated_wait = 0
        per_stop_waits = []

        # simulate bus
        for i in range(len(path) - 1):
            dist = get_distance(path[i], path[i + 1])
            sim_time += dist
            battery -= dist
            station = path[i + 1]

            if battery < 0:
                return float("-inf")

            if station in plan:
                chargers = temp_station_times[station]
                charger_index = chargers.index(min(chargers))
                available_time = chargers[charger_index]

                wait = max(0, available_time - sim_time)
                per_stop_waits.append(wait)
                estimated_wait += wait

                charge_end = max(sim_time, available_time) + CHARGE_TIME
                chargers[charger_index] = charge_end
                sim_time = charge_end
                battery = MAX_RANGE

        journey_duration = sim_time - int(bus.departure)

        station_backlogs = {}
        sim_time_check = int(bus.departure)
        for i in range(len(path) - 1):
            dist = get_distance(path[i], path[i + 1])
            sim_time_check += dist
            station = path[i + 1]
            if station in plan and station in original_station_times:
                earliest_free = min(original_station_times[station])
                station_backlogs[station] = max(0, earliest_free - sim_time_check)

        ctx = PlanContext(
            bus_id=bus.bus_id,
            operator=bus.operator,
            departure=int(bus.departure),
            estimated_wait=estimated_wait,
            per_stop_waits=per_stop_waits,
            journey_duration=journey_duration,
            stop_count=len(plan),
            operator_wait_time=operator_wait_time,
            station_backlogs=station_backlogs,
        )

        # use objective weights to score plan
        total = 0.0
        for objective in self.objectives:
            w = weights.get(objective.name)
            total += w * objective.score(ctx)

        return total

    # ------------------------------------------------------------------
    # Execute the chosen plan and commit charger state
    # ------------------------------------------------------------------

    def _execute_plan(self, bus, path, chosen_plan, station_free_time):
        events = []
        current_time = int(bus.departure)
        battery = MAX_RANGE

        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]

            dist = None
            for s, e, d in SEGMENTS:
                if (s, e) == (start, end) or (e, s) == (start, end):
                    dist = d
                    break

            if dist is None:
                raise Exception(f"Invalid segment {start}->{end}")

            current_time += dist
            arrival_time = current_time
            battery -= dist

            if battery < 0:
                raise Exception(f"Bus {bus.bus_id} exceeded range on {start}->{end}")

            if end in chosen_plan:
                chargers = station_free_time[end]
                charger_index = chargers.index(min(chargers))
                available_time = chargers[charger_index]
                charge_start = max(arrival_time, available_time)
                wait_time = charge_start - arrival_time
                charge_end = charge_start + CHARGE_TIME
                chargers[charger_index] = charge_end

                events.append(
                    ChargeEvent(
                        station=end,
                        arrival_time=arrival_time,
                        charge_start=charge_start,
                        charge_end=charge_end,
                        wait_time=wait_time,
                    )
                )

                current_time = charge_end
                battery = MAX_RANGE

        return events, current_time
