from dataclasses import dataclass
from typing import List


@dataclass
class Bus:
    bus_id: str
    operator: str
    source: str
    destination: str
    departure: int


@dataclass
class ChargeEvent:
    station: str
    arrival_time: int
    charge_start: int
    charge_end: int
    wait_time: int


@dataclass
class BusSchedule:
    bus_id: str
    source: str
    destination: str
    events: List[ChargeEvent]
    final_arrival_time: int
