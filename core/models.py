from dataclasses import dataclass


@dataclass
class Bus:
    bus_id: str
    operator: str
    source: str
    destination: str
    departure: str
