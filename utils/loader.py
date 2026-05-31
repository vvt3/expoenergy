import pandas as pd
from core.models import Bus


def load_scenario(path):
    df = pd.read_csv(path, index_col=False)

    buses = [Bus(**row) for row in df.to_dict("records")]

    return df, buses
