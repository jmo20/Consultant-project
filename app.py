
import streamlit as st
import pandas as pd
import uuid
from datetime import date
import os

st.set_page_config(page_title="Editable Consulting Dashboard", layout="wide")

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

st.title("🔧 Editable Consulting Management App")
tabs = st.tabs(["Overview", "Customers", "Consultants", "Forecasting", "Admin"])

# --- Overview ---
with tabs[0]:
    st.subheader("📊 Summary")
    col1, col2 = st.columns(2)
    col1.metric("Total Customers", len(st.session_state.customers))
    col2.metric("Total Consultants", len(st.session_state.consultants))

# --- Customers ---
with tabs[1]:
    st.subheader("🧾 All Customers (Editable)")
    for i, row in st.session_state.customers.iterrows():
        with st.expander(f"Customer {row['ID']} - {row['Industry']} / {row['Revenue Group']} [{row['Status']}]"):
            with st.form(f"edit_customer_{row['ID']}"):
                new_status = st.selectbox("Status", ["Prospective", "Assigned", "Canceled"], index=["Prospective", "Assigned", "Canceled"].index(row["Status"]))
                new_industry = st.selectbox("Industry", ["Tech", "Financial", "Retail", "Healthcare"], index=["Tech", "Financial", "Retail", "Healthcare"].index(row["Industry"]))
                new_revenue = st.selectbox("Revenue Group", ["< $10M", "$10M - $100M", "> $100M"], index=["< $10M", "$10M - $100M", "> $100M"].index(row["Revenue Group"]))
                new_assigned = st.text_input("Assigned Consultant", value=row["Assigned Consultant"])
                submit = st.form_submit_button("Save Changes")
                if submit:
                    st.session_state.customers.at[i, "Status"] = new_status
                    st.session_state.customers.at[i, "Industry"] = new_industry
                    st.session_state.customers.at[i, "Revenue Group"] = new_revenue
                    st.session_state.customers.at[i, "Assigned Consultant"] = new_assigned
                    st.success("Customer updated!")

# --- Consultants ---
with tabs[2]:
    st.subheader("🧑‍💼 All Consultants (Editable)")
    for i, row in st.session_state.consultants.iterrows():
        with st.expander(f"{row['Name']} - {row['Status']}"):
            with st.form(f"edit_consultant_{row['Name']}"):
                new_status = st.selectbox("Status", ["Active", "Pending", "On Hold"], index=0 if "Active" in row["Status"] else 1 if "Pending" in row["Status"] else 2)
                new_load = st.number_input("Current Load", value=int(row["Current Load"]), min_value=0)
                new_max = st.number_input("Max Capacity", value=int(row["Max Capacity"]), min_value=1)
                new_spec_ind = st.text_input("Specialty Industries", value=row["Specialty Industries"])
                new_spec_rev = st.text_input("Specialty Revenue Groups", value=row["Specialty Revenue Groups"])
                if "Pending" in row["Status"]:
                    start_date_input = st.date_input("Projected Start Date", value=date.today())
                else:
                    start_date_input = None
                submit = st.form_submit_button("Save Changes")
                if submit:
                    st.session_state.consultants.at[i, "Status"] = new_status if new_status != "Pending" else f"Pending - Starts {start_date_input}" if start_date_input else new_status
                    st.session_state.consultants.at[i, "Current Load"] = new_load
                    st.session_state.consultants.at[i, "Max Capacity"] = new_max
                    st.session_state.consultants.at[i, "Specialty Industries"] = new_spec_ind
                    st.session_state.consultants.at[i, "Specialty Revenue Groups"] = new_spec_rev
                    st.success("Consultant updated!")

# --- Forecast ---
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

# --- Admin ---
with tabs[4]:
    st.subheader("⚙️ Admin Panel")
    st.write("Combined editable data:")
    st.dataframe(st.session_state.customers, use_container_width=True)
    st.dataframe(st.session_state.consultants, use_container_width=True)
