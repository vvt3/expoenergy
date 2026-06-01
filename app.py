import streamlit as st
import pandas as pd
from utils.loader import load_scenario, load_scenario_config
from utils.time import parse_time_reverse
from core.scheduler import Scheduler


st.set_page_config(page_title="Bus Scheduler")
st.title("Exponent Energy Bus Scheduler")

configs = load_scenario_config()

scenario = st.selectbox(
    "Choose Scenario",
    [
        "scenario1",
        "scenario2",
        "scenario3",
        "scenario4",
        "scenario5",
    ],
)

csv_path = f"data/{scenario}.csv"
df, buses = load_scenario(csv_path)

weights = configs[scenario]["weights"]

st.subheader("Scenario Input")

st.dataframe(df, height=250, hide_index=True)

scheduler = Scheduler()
result = scheduler.schedule(buses, weights)

st.subheader("Schedule Output")

for bus in result:
    st.write(f"Bus: {bus.bus_id}")
    schedule = {
        "Station": [],
        "Arrival": [],
        # "Charge Start Time": [],
        "Departure": [],
        "Wait Time": [],
    }
    for e in bus.events:
        schedule["Station"].append(e.station)
        schedule["Arrival"].append(parse_time_reverse(e.arrival_time))
        # schedule["Charge Start Time"].append(e.charge_start)
        schedule["Departure"].append(parse_time_reverse(e.charge_end))
        schedule["Wait Time"].append(e.wait_time)
        # schedule["Wait Time"].append(parse_time_reverse(e.wait_time))
    df = pd.DataFrame(schedule)
    # st.dataframe(df, use_container_width=True, hide_index=True)
    st.dataframe(df, width="stretch", hide_index=True)
    st.write("Final:", parse_time_reverse(bus.final_arrival_time))
    st.write("---")
