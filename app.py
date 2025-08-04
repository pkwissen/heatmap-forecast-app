import sys
import os
import subprocess
import streamlit as st
from pathlib import Path
import pandas as pd
from modules import data_handler, forecaster, planner, shift_plan
import webbrowser
from datetime import date, timedelta

# -----------------------------
# 🧠 Safe base path handling
# -----------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
PROCESSED_PATH = DATA_DIR / "processed_data.xlsx"
TRANSFORMED_PATH = DATA_DIR / "transformed_data.xlsx"
TRANSFORMED_PHONE59_PATH = DATA_DIR / "transformed_Phone59.xlsx"
FORECAST_DATA_PATH = DATA_DIR / "forecast_data.xlsx"

# 👇 PATCH: Add root dir and submodules to import path
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "modules"))
sys.path.insert(0, str(BASE_DIR / "prophet"))

# -----------------------------
# 🚀 Auto-launch via streamlit run (if frozen)
# -----------------------------
if getattr(sys, 'frozen', False):
    script_path = str(BASE_DIR / 'app.py')
    webbrowser.open("http://localhost:8501")
    subprocess.Popen(["streamlit", "run", script_path])
    sys.exit()

# -----------------------------
# Streamlit UI starts here
# -----------------------------
st.set_page_config(page_title="Ticket Volume Heat Map", layout="wide")
st.title("Ticket Volume Heat Map")

# Session state setup
if 'forecast' not in st.session_state:
    st.session_state['forecast'] = None
if 'plans' not in st.session_state:
    st.session_state['plans'] = None
if "show_shift_summary" not in st.session_state:
    st.session_state.show_shift_summary = False
if "show_hourly_distribution" not in st.session_state:
    st.session_state.show_hourly_distribution = False

# File paths (use Path objects everywhere)
processed_path = PROCESSED_PATH
transformed_path = TRANSFORMED_PATH

# Upload or load data
use_new_data = st.radio(
    "Do you want to upload new raw data?",
    options=["Select...", "Yes", "No"],
    index=0
)

uploaded_file1 = uploaded_file2 = processed_df = xls = None

if use_new_data == "Yes":
    uploaded_file1 = st.file_uploader("Upload new raw data from Service Now (.xlsx)", type=["xlsx"])

    if uploaded_file1:
        try:
            st.success("✅ File uploaded successfully from Service Now!")
            raw_df = data_handler.transform_new_data(uploaded_file1, TRANSFORMED_PATH)
            processed_df = data_handler.merge_with_existing(transformed_path, processed_path)
            xls = pd.ExcelFile(processed_path)
        except Exception as e:
            st.error(f"❌ Error processing Service Now file: {e}")
            st.stop()
    else:
        st.warning("⚠️ Please upload Service Now file to continue.")
        st.stop()

    uploaded_file2 = st.file_uploader("Upload new raw data from Five9 (.csv)", type=["csv"])

    if uploaded_file2:
        try:
            st.success("✅ File uploaded successfully from Five9!")
            raw_df = data_handler.transform_data_59(uploaded_file2, TRANSFORMED_PHONE59_PATH)
            processed_df = data_handler.add_transformed_phone59_sheet(PROCESSED_PATH, TRANSFORMED_PHONE59_PATH, sheet_name="Phone59")
            xls = pd.ExcelFile(processed_path)
        except Exception as e:
            st.error(f"❌ Error processing Five9 file: {e}")
            st.stop()
    else:
        st.warning("⚠️ Please upload Five9 file to continue.")
        st.stop()

elif use_new_data == "No":
    if not processed_path.exists():
        st.error(f"❌ No processed data found at {processed_path}")
        st.stop()
    try:
        xls = pd.ExcelFile(processed_path)
    except Exception as e:
        st.error(f"❌ Failed to load processed file: {e}")
        st.stop()
else:
    st.info("ℹ️ Please select whether you want to upload new raw data or not.")
    st.stop()

# --- Forecast Period Selection ---
st.markdown("### Select Forecasting Period")

latest_data_date = xls.parse("Chat")["Date"].max().date()
earliest_data_date = xls.parse("Chat")["Date"].min().date()
today = pd.Timestamp.today().date()

future_limit = today + pd.Timedelta(days=120)

# Allow selection from earliest data or today, whichever is earlier
min_selectable = min(earliest_data_date, today)
max_selectable = max(latest_data_date, future_limit)

default_start = max(min_selectable, today)  # Default to today if earliest is in the past
default_end = min(default_start + pd.Timedelta(days=7), max_selectable)

start_date = st.date_input(
    "Start Date",
    value=default_start,
    min_value=min_selectable,
    max_value=max_selectable
)
end_date = st.date_input(
    "End Date",
    value=default_end,
    min_value=start_date,
    max_value=max_selectable
)

tasks_per_resource = {"Chat": 13, "Phone": 13, "Phone59": 13, "Self-service": 15}

# Run Forecast Button
run_forecast = st.button("🚀 Run Forecast & Generate Heat Map", use_container_width=True)

if run_forecast:
    st.info(f"📊 Forecasting for **{start_date.strftime('%b %d')}** to **{end_date.strftime('%b %d')}**")
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    progress = st.progress(0, text="🚀 Starting forecasting...")

    forecast_dfs = []
    channels = ["Chat", "Phone", "Phone59", "Self-service"]
    for i, channel in enumerate(channels):
        progress.progress((i + 1) * 20, text=f"⏳ Forecasting {channel}...")
        df = forecaster.run_forecasting(xls.parse(channel), start_dt, end_dt)
        df["Channel"] = channel
        forecast_dfs.append(df)

    full_forecast = pd.concat(forecast_dfs, ignore_index=True)
    st.session_state['forecast'] = full_forecast

    progress.progress(90, text="🗕️ Forecasting complete. Generating Heat Map...")
    shift_plans = planner.generate_shift_plan(full_forecast, tasks_per_resource=tasks_per_resource)
    st.session_state['plans'] = shift_plans
    progress.progress(100, text="✅ All done!")
    planner.apply_coloring_and_download(shift_plans, start_date, end_date, backup_path=FORECAST_DATA_PATH)

# Show saved heatmap if available
if st.session_state['plans'] is not None and not run_forecast:
    st.markdown("### Showing Heat Map")
    planner.apply_coloring_and_download(st.session_state['plans'], start_date, end_date)

# Shift Planning Views
st.markdown("---")
st.markdown("## 📋 View Shift Planning Details")

if st.button("📊 Show Shift Level Summary", use_container_width=True):
    st.session_state.show_shift_summary = True
if st.button("🕐 Show Final Hourly Distribution", use_container_width=True):
    st.session_state.show_hourly_distribution = True

if st.session_state.show_shift_summary or st.session_state.show_hourly_distribution:
    shift_file_path = FORECAST_DATA_PATH
    try:
        summary_df, hourly_df = shift_plan.main_pipeline(shift_file_path)

        if st.session_state.show_shift_summary:
            st.subheader("🔹 Shift Level Summary")
            st.dataframe(summary_df)

        if st.session_state.show_hourly_distribution:
            st.subheader("🔸 Final Hourly Distribution")
            st.dataframe(hourly_df)

    except Exception as e:
        st.error(f"❌ Failed to generate shift plan from file: {e}")
