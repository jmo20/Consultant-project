
import streamlit as st
import pandas as pd
import uuid
from datetime import date
import os

st.set_page_config(page_title="Consulting Management App", layout="wide")

# --- Load Dummy Data or Files ---
@st.cache
def load_data():
    try:
        customers = pd.read_csv("dummy_customers.csv")
    except Exception:
        customers = pd.DataFrame([{
            "ID": str(uuid.uuid4())[:8],
            "Industry": "Tech",
            "Revenue Group": "$10M - $100M",
            "Status": "Unassigned",
            "Assigned Consultant": ""
        }])

    try:
        consultants = pd.read_csv("dummy_consultants.csv")
    except Exception:
        consultants = pd.DataFrame([{
            "Name": "Consultant 1",
            "Specialty Industries": "Tech",
            "Specialty Revenue Groups": "$10M - $100M",
            "Current Load": 0,
            "Max Capacity": 8,
            "Status": "Active"
        }])
    return customers, consultants

if "customers" not in st.session_state:
    st.session_state.customers, st.session_state.consultants = load_data()

# Sidebar - Add Data
st.sidebar.header("Add Data")

with st.sidebar.expander("➕ Add Customer"):
    industry = st.selectbox("Industry", ["Tech", "Financial", "Retail", "Healthcare"])
    revenue = st.selectbox("Revenue Group", ["< $10M", "$10M - $100M", "> $100M"])
    if st.button("Add Customer"):
        new_customer = {
            "ID": str(uuid.uuid4())[:8],
            "Industry": industry,
            "Revenue Group": revenue,
            "Status": "Unassigned",
            "Assigned Consultant": ""
        }
        st.session_state.customers = pd.concat([st.session_state.customers, pd.DataFrame([new_customer])], ignore_index=True)

with st.sidebar.expander("➕ Add Consultant"):
    name = st.text_input("Consultant Name")
    spec_ind = st.multiselect("Specialty Industries", ["Tech", "Financial", "Retail", "Healthcare"])
    spec_rev = st.multiselect("Specialty Revenue Groups", ["< $10M", "$10M - $100M", "> $100M"])
    max_cap = st.number_input("Max Capacity", min_value=1, max_value=20, value=8, step=1)
    if st.button("Add Consultant"):
        new_consultant = {
            "Name": name,
            "Specialty Industries": ", ".join(spec_ind),
            "Specialty Revenue Groups": ", ".join(spec_rev),
            "Current Load": 0,
            "Max Capacity": max_cap,
            "Status": "Active"
        }
        st.session_state.consultants = pd.concat([st.session_state.consultants, pd.DataFrame([new_consultant])], ignore_index=True)

def assign_customer(customer_id):
    customer = st.session_state.customers.loc[st.session_state.customers["ID"] == customer_id].iloc[0]
    matches = st.session_state.consultants[
        (st.session_state.consultants["Status"].str.contains("Active")) &
        (st.session_state.consultants["Current Load"] < st.session_state.consultants["Max Capacity"]) &
        (st.session_state.consultants["Specialty Industries"].str.contains(customer["Industry"])) &
        (st.session_state.consultants["Specialty Revenue Groups"].str.contains(customer["Revenue Group"]))
    ]
    if not matches.empty:
        consultant_idx = matches.index[0]
        consultant_name = matches.loc[consultant_idx, "Name"]
        st.session_state.customers.loc[st.session_state.customers["ID"] == customer_id, "Status"] = "Assigned"
        st.session_state.customers.loc[st.session_state.customers["ID"] == customer_id, "Assigned Consultant"] = consultant_name
        st.session_state.consultants.at[consultant_idx, "Current Load"] += 1
        st.success(f"Assigned {customer_id} to {consultant_name}")
    else:
        st.warning(f"No available consultant match for {customer_id}.")
        with st.expander("📋 Create Hiring Requisition"):
            start_date = st.date_input("Projected Start Date", value=date.today())
            if st.button("Add Hiring Req"):
                req = {
                    "Name": f"Hiring Req #{len(st.session_state.consultants)+1}",
                    "Specialty Industries": customer["Industry"],
                    "Specialty Revenue Groups": customer["Revenue Group"],
                    "Current Load": 0,
                    "Max Capacity": 8,
                    "Status": f"Pending - Starts {start_date}"
                }
                st.session_state.consultants = pd.concat([st.session_state.consultants, pd.DataFrame([req])], ignore_index=True)
                st.success("Hiring requisition created.")

st.title("📊 Consulting Management Dashboard")
tabs = st.tabs(["Overview", "Customer Queue", "Consultants", "Wait Estimator"])

# Tab 1: Overview
with tabs[0]:
    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Prospective Customers", len(st.session_state.customers))
    col2.metric("Active Consultants", st.session_state.consultants[st.session_state.consultants["Status"].str.contains("Active")].shape[0])
    col3.metric("Total Assignments", st.session_state.consultants["Current Load"].sum())

# Tab 2: Customer Queue
with tabs[1]:
    st.subheader("🧾 Prospective Customer Queue")
    unassigned = st.session_state.customers[st.session_state.customers["Status"] == "Unassigned"]
    for _, row in unassigned.iterrows():
        with st.expander(f"{row['ID']} - {row['Industry']} / {row['Revenue Group']}"):
            st.write("Status:", row["Status"])
            if st.button(f"Assign {row['ID']}"):
                assign_customer(row["ID"])
    st.subheader("All Customers")
    st.dataframe(st.session_state.customers, use_container_width=True)

# Tab 3: Consultants
with tabs[2]:
    st.subheader("🧑‍💼 Consultant Roster")
    st.dataframe(st.session_state.consultants, use_container_width=True)

# Tab 4: Wait Estimator
with tabs[3]:
    st.subheader("⏳ Wait Time Estimator")
    segs = st.session_state.customers[st.session_state.customers["Status"] == "Unassigned"].groupby(["Industry", "Revenue Group"]).size().reset_index(name="Customers Waiting")
    capacity = st.session_state.consultants.copy()
    capacity["Available Slots"] = capacity["Max Capacity"] - capacity["Current Load"]
    capacity_summary = capacity[capacity["Status"].str.contains("Active")]
    total_slots = capacity_summary["Available Slots"].sum()
    st.write(f"Total Available Consultant Slots: {total_slots}")
    st.dataframe(segs, use_container_width=True)
    if segs["Customers Waiting"].sum() > total_slots:
        st.warning("⚠️ Not enough consultant capacity. Hiring needed!")
    else:
        st.success("✅ Current capacity can support demand.")
