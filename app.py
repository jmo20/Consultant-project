
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import uuid
from datetime import date

st.set_page_config(page_title="Consulting Management - AgGrid", layout="wide")

@st.cache_data
def load_data():
    try:
        customers = pd.read_csv("dummy_customers.csv")
    except:
        customers = pd.DataFrame(columns=["ID", "Industry", "Revenue Group", "Status", "Assigned Consultant"])
    try:
        consultants = pd.read_csv("dummy_consultants.csv")
    except:
        consultants = pd.DataFrame(columns=["Name", "Specialty Industries", "Specialty Revenue Groups", "Current Load", "Max Capacity", "Status"])
    return customers, consultants

if "customers" not in st.session_state:
    st.session_state.customers, st.session_state.consultants = load_data()

st.title("📊 Consulting Management - AgGrid Inline Editor")
tabs = st.tabs(["Overview", "Customers", "Consultants", "Forecast"])

with tabs[0]:
    st.subheader("Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Customers", len(st.session_state.customers))
    col2.metric("Total Consultants", len(st.session_state.consultants))

with tabs[1]:
    st.subheader("🧾 Customers - Inline Editable")
    gb = GridOptionsBuilder.from_dataframe(st.session_state.customers)
    gb.configure_default_column(editable=True)
    gb.configure_grid_options(domLayout='normal')
    grid_response = AgGrid(
        st.session_state.customers,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        height=400,
        fit_columns_on_grid_load=True
    )
    st.session_state.customers = grid_response['data']

with tabs[2]:
    st.subheader("🧑‍💼 Consultants - Inline Editable")
    gb2 = GridOptionsBuilder.from_dataframe(st.session_state.consultants)
    gb2.configure_default_column(editable=True)
    gb2.configure_grid_options(domLayout='normal')
    grid_response2 = AgGrid(
        st.session_state.consultants,
        gridOptions=gb2.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        height=400,
        fit_columns_on_grid_load=True
    )
    st.session_state.consultants = grid_response2['data']

def forecast_wait_time(industry, revenue_group):
    active = st.session_state.consultants[
        (st.session_state.consultants["Status"].str.contains("Active")) &
        (st.session_state.consultants["Current Load"] < st.session_state.consultants["Max Capacity"]) &
        (st.session_state.consultants["Specialty Industries"].str.contains(industry)) &
        (st.session_state.consultants["Specialty Revenue Groups"].str.contains(revenue_group))
    ]
    if not active.empty:
        return "0 weeks"
    pending = st.session_state.consultants[st.session_state.consultants["Status"].str.contains("Pending")]
    pending["Start Date"] = pending["Status"].str.extract(r"Starts (.*)")
    pending["Start Date"] = pd.to_datetime(pending["Start Date"], errors="coerce")
    filtered = pending[
        (pending["Specialty Industries"].str.contains(industry)) &
        (pending["Specialty Revenue Groups"].str.contains(revenue_group))
    ]
    if not filtered.empty:
        soonest = filtered["Start Date"].min()
        if pd.notnull(soonest):
            delta_weeks = (soonest.date() - date.today()).days // 7
            return f"{max(delta_weeks, 0)} week(s)"
    return "Need more prospective consultants"

with tabs[3]:
    st.subheader("⏳ Wait Time Forecast")
    for _, row in st.session_state.customers.iterrows():
        if row["Status"] != "Assigned":
            with st.expander(f"{row['ID']} - {row['Industry']} / {row['Revenue Group']}"):
                st.write("Forecast:", forecast_wait_time(row["Industry"], row["Revenue Group"]))
