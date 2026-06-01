from core.models import BusSchedule, ChargeEvent
from core.route import build_path, route_distance, SEGMENTS
from core.route import CHARGE_TIME


class Scheduler:
    def schedule(self, buses):
        schedules = []

        for bus in buses:
            path = build_path(bus.source, bus.destination)

            events = []
            current_time = int(bus.departure)

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

                # TEMP: charge at every station
                if end != bus.destination:
                    charge_start = arrival_time
                    charge_end = charge_start + CHARGE_TIME

                    events.append(
                        ChargeEvent(
                            station=end,
                            arrival_time=arrival_time,
                            charge_start=charge_start,
                            charge_end=charge_end,
                            wait_time=0,
                        )
                    )

                    current_time = charge_end

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
