import pandas as pd
from core.models import Bus
from utils.time import parse_time


def load_scenario(path):
    df = pd.read_csv(path, index_col=False)

    buses = [
        Bus(
            bus_id=row["bus_id"],
            operator=row["operator"],
            source=row["source"],
            destination=row["destination"],
            departure=parse_time(row["departure"]),
        )
        for row in df.to_dict("records")
    ]

    return df, buses
