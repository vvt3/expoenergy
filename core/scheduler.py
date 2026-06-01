from core.models import BusSchedule, ChargeEvent
from core.route import build_path, generate_valid_plans, get_distance
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
            print(bus.bus_id)
            print(station_free_time)

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

                # Error checks
                if battery < 0:
                    raise Exception("invalid schedule, Bus exceeded its range")
                if chosen_plan is None:
                    raise Exception(f"No valid charging plan found for {bus.bus_id}")

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
        best_plan = None
        best_score = float("-inf")

        for plan in plans:
            score = self.score_plan(
                bus,
                plan,
                weights,
                station_free_time,
                operator_wait_time,
            )

            if score > best_score:
                best_score = score
                best_plan = plan

        print(f"{bus.bus_id} SELECTED {best_plan} score={best_score}")

        return best_plan

    def score_plan(
        self,
        bus,
        plan,
        weights,
        station_free_time,
        operator_wait_time,
    ):
        battery = MAX_RANGE

        temp_station_times = {
            station: times.copy() for station, times in station_free_time.items()
        }
        estimated_wait = 0

        path = build_path(bus.source, bus.destination)
        sim_time = int(bus.departure)

        for i in range(len(path) - 1):
            dist = get_distance(path[i], path[i + 1])
            sim_time += dist
            station = path[i + 1]

            battery -= dist
            if battery < 0:
                return float("-inf")
            remaining_range = battery
            print(
                bus.bus_id,
                station,
                f"arrival={sim_time}",
                f"battery={remaining_range}",
            )

            if station in plan:
                chargers = temp_station_times[station]
                charger_index = chargers.index(min(chargers))
                available_time = chargers[charger_index]

                wait = max(0, available_time - sim_time)
                # print(
                #     f"{bus.bus_id}",
                #     f"station={station}",
                #     f"arrival={sim_time}",
                #     f"charger_times={chargers}",
                #     f"available={available_time}",
                #     f"wait={wait}",
                # )
                estimated_wait += wait

                charge_start = sim_time + wait
                charge_end = charge_start + CHARGE_TIME

                chargers[charger_index] = charge_end

                sim_time = charge_end
                battery = MAX_RANGE  # reset the battery

        stop_count = len(plan)

        # scoring
        # INDIVIDUAL
        arrival_penalty = sim_time
        individual_score = (
            -(estimated_wait * 100)
            - (stop_count * CHARGE_TIME)
            - (arrival_penalty * 0.1)
        )

        # OPERATOR
        # operator_score = -(operator_wait_time.get(bus.operator, 0) * 1000)
        operator_score = 0

        # OVERALL
        congestion_penalty = 0

        for station, chargers in temp_station_times.items():
            congestion_penalty += max(chargers)
        overall_score = -congestion_penalty

        # print(
        #     bus.bus_id,
        #     plan,
        #     "stops=",
        #     stop_count,
        #     "wait=",
        #     estimated_wait,
        #     "score=",
        #     (
        #         weights["individual"] * individual_score
        #         + weights["operator"] * operator_score
        #         + weights["overall"] * overall_score
        #     ),
        # )

        return (
            weights["individual"] * individual_score
            + weights["operator"] * operator_score
            + weights["overall"] * overall_score
        )
