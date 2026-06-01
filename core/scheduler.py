from core.models import BusSchedule, ChargeEvent
from core.route import build_path, generate_valid_plans
from core.route import CHARGE_TIME, MAX_RANGE, STATIONS, SEGMENTS


class Scheduler:
    def schedule(self, buses, weights):
        schedules = []
        station_free_time = {
            station: [0] * chargers for station, chargers in STATIONS.items()
        }
        operator_wait_time = {}

        # Sort incase of unsorted
        buses = sorted(buses, key=lambda b: b.departure)

        for bus in buses:
            path = build_path(bus.source, bus.destination)
            plans = generate_valid_plans(path)
            chosen_plan = self.choose_plan(
                bus,
                plans,
                weights,
                station_free_time,
                operator_wait_time,
            )

            events = []
            current_time = int(bus.departure)
            battery = MAX_RANGE

            # travel segment by segment
            for i in range(len(path) - 1):
                start = path[i]
                end = path[i + 1]

                # find distance
                dist = None
                for s, e, d in SEGMENTS:
                    if (s, e) == (start, end) or (e, s) == (start, end):
                        dist = d
                        break

                if dist is None:
                    raise Exception(f"Invalid segment {start}->{end}")

                # move bus
                current_time += dist
                arrival_time = current_time
                battery -= dist

                if battery < 0:
                    raise Exception("invalid schedule, Bus exceeded its range")

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
                    battery = 240

            total_wait = sum(event.wait_time for event in events)
            operator_wait_time.setdefault(bus.operator, 0)
            operator_wait_time[bus.operator] += total_wait

            final_arrival = current_time

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

    def choose_plan(
        self,
        bus,
        plans,
        weights,
        station_free_time,
        operator_wait_time,
    ):
        return max(
            plans,
            key=lambda p: self.score_plan(
                bus,
                p,
                weights,
                station_free_time,
                operator_wait_time,
            ),
        )

    def score_plan(
        self,
        bus,
        plan,
        weights,
        station_free_time,
        operator_wait_time,
    ):

        stop_count = len(plan)
        congestion = 0
        for station in plan:
            congestion += min(station_free_time[station])

        # scoring
        individual_score = -stop_count
        operator_score = -operator_wait_time.get(
            bus.operator,
            0,
        )
        overall_score = -congestion

        return (
            weights["individual"] * individual_score
            + weights["operator"] * operator_score
            + weights["overall"] * overall_score
        )
