import streamlit as st
from datetime import date
from src.database.utils import db_ops

st.title("📅 Daily Habit Log")

# Select the date to log habits for (default today)
log_date = st.date_input("Select Date", value=date.today())

# Fetch all habits
habits = db_ops.list_all_habits()

# We'll gather log entries in a dict habit_id -> value
log_values = {}

# Fetch existing logs for that date for all habits to pre-fill the inputs
logs_query = db_ops.get_habit_logs_for_day(log_date)
existing_logs = {row.habit_id: row.value for row in logs_query}

st.write(f"### Log habits for {log_date.isoformat()}")

# Create a form to batch submit logs
with st.form("habit_log_form"):
    for habit in habits:
        habit_id = habit.id
        habit_name = habit.name
        is_binary = habit.is_binary_habit

        current_val = existing_logs.get(habit_id, 0.0)

        if is_binary:
            # Show checkbox, checked if current_val == 1.0
            checked = st.checkbox(habit_name, value=(current_val == 1.0), key=str((habit_id, log_date)))
            log_values[habit_id] = 1.0 if checked else 0.0
        else:
            # Show numeric input
            val = st.number_input(
                habit_name,
                value=current_val,
                step=0.1,
                format="%.2f",
                key=str((habit_id, log_date))
            )
            log_values[habit_id] = val

    submitted = st.form_submit_button("Save Logs")

    if submitted:
        db_ops.add_habit_logs(log_date, log_values)
        st.success(f"Habit logs for {log_date.isoformat()} saved!")
