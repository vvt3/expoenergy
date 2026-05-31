import streamlit as st
from utils.loader import load_scenario

buses = load_scenario("data/scenario1.csv")

st.title("Bus Scheduler")

st.write(buses)
