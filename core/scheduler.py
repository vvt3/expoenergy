from core.models import BusSchedule, ChargeEvent
from core.route import build_path, compute_stops, get_next_distance, SEGMENTS
from core.route import CHARGE_TIME, MAX_RANGE


class Scheduler:
    def schedule(self, buses):
        schedules = []

        station_free_time = {"A": 0, "B": 0, "C": 0, "D": 0}

        for bus in buses:
            path = build_path(bus.source, bus.destination)

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
                if i < len(path) - 1:
                    next_dist = get_next_distance(path, i)
                else:
                    next_dist = None

                if battery < 0:
                    raise Exception("invalid schedule, Bus exceeded its range")

                if (
                    next_dist is not None
                    and battery < next_dist
                    and end != bus.destination
                ):
                    available_time = station_free_time[end]
                    charge_start = max(arrival_time, available_time)
                    wait_time = charge_start - arrival_time
                    charge_end = charge_start + CHARGE_TIME
                    station_free_time[end] = charge_end

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
