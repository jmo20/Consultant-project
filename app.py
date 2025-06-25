
import streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime
import os

st.set_page_config(page_title="Enhanced Consulting Management App", layout="wide")

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

st.sidebar.header("Add Data")

with st.sidebar.expander("➕ Add Prospective Customer"):
    industry = st.selectbox("Industry", ["Tech", "Financial", "Retail", "Healthcare"])
    revenue = st.selectbox("Revenue Group", ["< $10M", "$10M - $100M", "> $100M"])
    if st.button("Add Prospective Customer"):
        new_customer = {
            "ID": str(uuid.uuid4())[:8],
            "Industry": industry,
            "Revenue Group": revenue,
            "Status": "Prospective",
            "Assigned Consultant": ""
        }
        st.session_state.customers = pd.concat([st.session_state.customers, pd.DataFrame([new_customer])], ignore_index=True)

with st.sidebar.expander("➕ Add Consultant"):
    name = st.text_input("Consultant Name")
    spec_ind = st.multiselect("Specialty Industries", ["Tech", "Financial", "Retail", "Healthcare"])
    spec_rev = st.multiselect("Specialty Revenue Groups", ["< $10M", "$10M - $100M", "> $100M"])
    max_cap = st.number_input("Max Capacity", min_value=1, max_value=20, value=8, step=1)
    start_date = st.date_input("Start Date", value=date.today())
    if st.button("Add Consultant or Hiring Req"):
        status = "Active" if start_date <= date.today() else f"Pending - Starts {start_date}"
        new_consultant = {
            "Name": name if name else f"Hiring Req #{len(st.session_state.consultants) + 1}",
            "Specialty Industries": ", ".join(spec_ind),
            "Specialty Revenue Groups": ", ".join(spec_rev),
            "Current Load": 0,
            "Max Capacity": max_cap,
            "Status": status
        }
        st.session_state.consultants = pd.concat([st.session_state.consultants, pd.DataFrame([new_consultant])], ignore_index=True)

def forecast_wait_time(industry, revenue_group):
    active = st.session_state.consultants[
        (st.session_state.consultants["Status"].str.contains("Active")) &
        (st.session_state.consultants["Current Load"] < st.session_state.consultants["Max Capacity"]) &
        (st.session_state.consultants["Specialty Industries"].str.contains(industry)) &
        (st.session_state.consultants["Specialty Revenue Groups"].str.contains(revenue_group))
    ]
    if not active.empty:
        return "0 weeks (immediate capacity available)"

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
            return f"Est. {delta_weeks} week(s) (based on pending hire)"
    return "Need more prospective consultants to forecast wait time"

st.title("🚀 Enhanced Consulting Management Dashboard")
tabs = st.tabs(["Overview", "Customers", "Consultants", "Forecasting"])

with tabs[0]:
    st.subheader("🔎 Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Customers", len(st.session_state.customers))
    col2.metric("Total Consultants (Incl. Hiring Reqs)", len(st.session_state.consultants))

with tabs[1]:
    st.subheader("📋 All Customers (Active & Prospective)")
    st.dataframe(st.session_state.customers, use_container_width=True)

with tabs[2]:
    st.subheader("🧑‍💼 All Consultants (Active & Pending)")
    st.dataframe(st.session_state.consultants, use_container_width=True)

with tabs[3]:
    st.subheader("⏳ Wait Time Forecast")
    unassigned = st.session_state.customers[st.session_state.customers["Status"] != "Assigned"]
    for _, row in unassigned.iterrows():
        with st.expander(f"Customer {row['ID']} - {row['Industry']} / {row['Revenue Group']}"):
            wait = forecast_wait_time(row["Industry"], row["Revenue Group"])
            st.write("Estimated Wait Time:", wait)
