import streamlit as st
import pandas as pd
from utils.loader import load_scenario, load_scenario_config
from utils.time import parse_time_reverse
from core.scheduler import Scheduler

st.set_page_config(page_title="Bus Scheduler", layout="wide")
st.title("Exponent Energy Bus Scheduler")

configs = load_scenario_config()

col_left, col_right = st.columns([1, 3])

with col_left:
    scenario = st.selectbox(
        "Scenario", ["scenario1", "scenario2", "scenario3", "scenario4", "scenario5"]
    )
    weights = configs[scenario]["weights"]

    st.markdown("**Weights**")
    w_individual = st.slider(
        "Individual", 0.0, 10.0, float(weights["individual"]), step=0.5
    )
    w_operator = st.slider("Operator", 0.0, 10.0, float(weights["operator"]), step=0.5)
    w_overall = st.slider("Overall", 0.0, 10.0, float(weights["overall"]), step=0.5)
    weights = {"individual": w_individual, "operator": w_operator, "overall": w_overall}

csv_path = f"data/{scenario}.csv"
df_input, buses = load_scenario(csv_path)

scheduler = Scheduler()
result = scheduler.schedule(buses, weights)

with col_right:
    tab_input, tab_buses, tab_stations = st.tabs(["Input", "Per-Bus", "Per-Station"])

    with tab_input:
        st.dataframe(df_input, width="stretch", hide_index=True)

    with tab_buses:
        for bus in result:
            total_wait = sum(e.wait_time for e in bus.events)
            label = f"{bus.bus_id}  →  arrives {parse_time_reverse(bus.final_arrival_time)}  |  wait {total_wait} min"
            with st.expander(label):
                rows = [
                    {
                        "Station": e.station,
                        "Arrival": parse_time_reverse(e.arrival_time),
                        "Departure": parse_time_reverse(e.charge_end),
                        "Wait (min)": e.wait_time,
                    }
                    for e in bus.events
                ]
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    with tab_stations:
        for station in ["A", "B", "C", "D"]:
            charges = []
            for bus in result:
                for e in bus.events:
                    if e.station == station:
                        charges.append(
                            {
                                "Bus": bus.bus_id,
                                "Operator": next(
                                    b.operator for b in buses if b.bus_id == bus.bus_id
                                ),
                                "Arrival": parse_time_reverse(e.arrival_time),
                                "Start": parse_time_reverse(e.charge_start),
                                "Done": parse_time_reverse(e.charge_end),
                                "Wait (min)": e.wait_time,
                            }
                        )
            charges.sort(key=lambda x: x["Start"])
            with st.expander(f"Station {station}  —  {len(charges)} buses"):
                if charges:
                    st.dataframe(
                        pd.DataFrame(charges), width="stretch", hide_index=True
                    )
                else:
                    st.write("No buses charged here.")
