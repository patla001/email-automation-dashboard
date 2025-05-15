import json
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime

# CONFIGURATION
DEFAULT_LOG_PATH = "sent_responses_log.json"


# PAGE SETUP
st.set_page_config(page_title="📬 Email System Dashboard", layout="wide")
st.title("📬 Email Automation Assessment Dashboard")
st.caption("Monitoring classification, delivery, and system behavior")

# SIDEBAR OPTIONS
st.sidebar.header("📂 Load JSON Log File")
uploaded_file = st.sidebar.file_uploader("Upload a JSON log file", type="json")

# load data function
def load_data(file):
    try:
        if file:
            data = json.load(file)
        else:
            with open(DEFAULT_LOG_PATH, "r") as f:
                data = json.load(f)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to load JSON log: {e}")
        return pd.DataFrame([])
# load data
df = load_data(uploaded_file)
# if no data is loaded, then stop the execution
if df.empty:
    st.warning("No data to display. Upload or generate data to proceed.")
    st.stop()

# DATA CLEANUP
# timestamp conversion
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

# SIDEBAR FILTERS
# Add filters for status and classification
st.sidebar.header("🔍 Filters")
status_options = df["status"].dropna().unique().tolist()
status_filter = st.sidebar.multiselect("Status", options=status_options, default=status_options)
# clean up classification options
classification_options = df["classification"].dropna().unique().tolist()
classification_filter = st.sidebar.multiselect("Classification", options=classification_options, default=classification_options)

# APPLY FILTERS
# Filter the DataFrame based on selected status and classification
filtered_df = df[
    (df["status"].isin(status_filter)) &
    (df["classification"].isin(classification_filter))
]

# SUMMARY STATS
# Display summary statistics and the number of emails processed
st.markdown("## 🔢 Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Emails", len(df))
col2.metric("Errors", (df["status"] == "error").sum(), delta=f"{(df['status'] == 'error').mean()*100:.1f}%")
col3.metric("Successes", (df["status"] == "success").sum(), delta=f"{(df['status'] == 'success').mean()*100:.1f}%")
col4.metric("Unique Classifications", df["classification"].nunique())

# CHARTS
# Display a bar chart for status distribution
if not df["classification"].dropna().empty:
    st.markdown("## 📊 Classifications Overview")
    chart_data = df["classification"].value_counts().reset_index()
    chart_data.columns = ["classification", "count"]
    bar_chart = alt.Chart(chart_data).mark_bar().encode(
        x="classification", y="count", color="classification", tooltip=["classification", "count"]
    ).properties(height=300)
    st.altair_chart(bar_chart, use_container_width=True)

# RECENT LOG TABLE
# Display the most recent emails processed
st.markdown("## 📋 Recent Email Log")
st.dataframe(filtered_df.sort_values("timestamp", ascending=False), use_container_width=True)

# EXPORT BUTTON
# Download filtered data as CSV
st.download_button("📥 Download Filtered as CSV", data=filtered_df.to_csv(index=False), file_name="filtered_email_log.csv")

# RAW JSON
# Display the raw JSON data in an expander
with st.expander("🧾 View Raw JSON Data"):
    st.json(df.to_dict(orient="records"))

# FOOTER
# Add a footer with the last updated timestamp
st.markdown("---")
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

