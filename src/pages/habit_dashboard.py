import calmap
import streamlit as st
import pandas as pd
import plotly.express as px
from matplotlib import pyplot as plt
from src.database.utils import db_ops

st.set_page_config(page_title="Habit Dashboard", layout="wide")

habits = db_ops.list_all_habits()

# Sidebar Habit Selector
st.sidebar.title("Habit Dashboard")
habit_options = {habit.name: habit for habit in habits}

if not habit_options:
    st.warning("No habits found. Please add a habit first.")
    st.stop()

selected_habit_name = st.sidebar.selectbox("Select a Habit", list(habit_options.keys()))
selected_habit = habit_options[selected_habit_name]

# Display Habit Info
st.title(f"📊 Habit: {selected_habit.name}")
st.markdown(f"**Description**: {selected_habit.description}")
st.markdown(f"**Binary**: {'Yes' if selected_habit.is_binary_habit else 'No'}")
st.markdown(f"**Negative Habit**: {'Yes' if selected_habit.is_negative_habit else 'No'}")
st.markdown(f"**Target**: {selected_habit.target_frequency_value} {selected_habit.target_frequency_unit} every {selected_habit.target_period_in_days} day(s)")

# Fetch Habit Logs
logs = db_ops.get_habit_logs_for_day  # alias

# Gather all logs for this habit
all_logs = db_ops.get_habit_logs_by_habit(selected_habit.id)

if not all_logs:
    st.info("No logs found for this habit.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame([
    {"Date": log.log_date, "Value": log.value}
    for log in all_logs
])
df["Date"] = pd.to_datetime(df["Date"])

# Line Chart
if not selected_habit.is_binary_habit:
    fig = px.line(df, x="Date", y="Value", markers=True,
                  title="Habit Progress Over Time",
                  labels={"Value": "Logged Value", "Date": "Date"})
    st.plotly_chart(fig, use_container_width=True)

# region Summary Stats
st.subheader("Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Logs", len(df))
col2.metric("Average Value", round(df["Value"].mean(), 2))
col3.metric("Most Recent", df["Date"].max().strftime('%Y-%m-%d'))
# endregion

# region Heat Map
df = df.set_index("Date")
daily_values = df['Value']

st.title("Habit Tracker - GitHub-style Contribution Heatmap")

# Plot the heatmap using calmap
fig, ax = plt.subplots(figsize=(16, 5))

if selected_habit.is_binary_habit:
    from matplotlib.colors import LinearSegmentedColormap
    red_to_green = LinearSegmentedColormap.from_list('SoftRedGreen', ["#c95757", "#57c959"])
    green_to_red = red_to_green.reversed()
    cmap = green_to_red if selected_habit.is_negative_habit else red_to_green
    calmap.yearplot(daily_values, ax=ax, vmin=0, vmax=1, cmap=cmap, linewidth=3, fillcolor='#f0f0f0', linecolor='white')
else:
    cmap = "Reds" if selected_habit.is_negative_habit else "Greens"
    calmap.yearplot(daily_values, ax=ax, cmap=cmap, linewidth=3, fillcolor='#a8a8a8', linecolor='white')

st.pyplot(fig)
# endregion

# Raw Data
with st.expander("📋 Show Raw Log Data"):
    st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)
