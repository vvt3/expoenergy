import pandas as pd
from core.models import Bus
from utils.time import parse_time
import json


def load_scenario(path):
    df = pd.read_csv(path, index_col=False)

    buses = [
        Bus(
            bus_id=row["bus_id"],
            operator=row["operator"],
            source=row["source"].strip().lower(),
            destination=row["destination"].strip().lower(),
            departure=parse_time(row["departure"]),
        )
        for row in df.to_dict("records")
    ]

    return df, buses


def load_scenario_config():
    with open("data/scenario_config.json") as f:
        return json.load(f)
