import streamlit as st
from utils.loader import load_scenario
from core.scheduler import Scheduler

st.set_page_config(page_title="Bus Scheduler")
st.title("Exponent Energy Bus Scheduler")

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

st.subheader("Scenario Input")

st.dataframe(df, height=250)

scheduler = Scheduler()
result = scheduler.schedule(buses)

st.subheader("Schedule Output")

for bus in result:
    st.write(bus.bus_id)
    for e in bus.events:
        st.write(e)
    st.write("Final:", bus.final_arrival_time)
    st.write("---")
