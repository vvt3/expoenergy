from core.models import BusSchedule, ChargeEvent
from core.route import build_path, generate_valid_plans, SEGMENTS
from core.route import CHARGE_TIME, MAX_RANGE


class Scheduler:
    def schedule(self, buses, weights):
        schedules = []
        station_free_time = {"A": 0, "B": 0, "C": 0, "D": 0}

        for bus in buses:
            path = build_path(bus.source, bus.destination)
            plans = generate_valid_plans(path)
            chosen_plan = self.choose_plan(plans, weights)

            print(bus.bus_id, chosen_plan)

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
                    available_time = station_free_time[end]
                    charge_start = max(arrival_time, available_time)
                    wait_time = charge_start - arrival_time
                    charge_end = charge_start + CHARGE_TIME
                    station_free_time[end] = charge_end

                    print(bus.bus_id, "arrived at", end)
                    print(bus.bus_id, "charging at", end, "battery:", battery)

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

    def choose_plan(self, plans, weights):
        return max(plans, key=lambda p: self.score_plan(p, weights))

    def score_plan(self, plan, weights):
        stop_count = len(plan)
        individual_score = -stop_count
        operator_score = 0
        overall_score = -stop_count

        return (
            weights["individual"] * individual_score
            + weights["operator"] * operator_score
            + weights["overall"] * overall_score
        )
