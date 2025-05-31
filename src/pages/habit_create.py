# """
# Defaults to habits dashboard
#
# - create_habit -> pop up from to create a new habit
# - show list of habits
#     - option to edit each habit
# - Select any habit -> Loads the habits dashboards
# """
#
#
# import streamlit as st
#
#
# @st.dialog('Create Habit')
# def create_habit():
#     with st.form("Create Habit", clear_on_submit=True):
#
#         st.text_input('Habit Name', key='habit_name')
#         st.checkbox('Binary Habit', key='is_binary')
#
#         st.number_input('Habit Target Value', key='habit_target_value')
#         st.text_input('Habit Unit(s)', key='habit_units')
#         st.number_input('Habit Target Period (in Days)', key='habit_target_period_in_days')
#
#         st.checkbox('Negative Habit', key='is_negative')
#
#         st.form_submit_button("Create Habit")
#
#
#
# st.button('Create Habit', on_click=create_habit)


import streamlit as st
from src.database.utils import DbOps, db_ops  # Update with your actual import path

# # Instantiate DB
# db = DbOps()

st.title("🌀 Create a New Habit")

with st.form("habit_form", clear_on_submit=True):
    name = st.text_input("Habit Name", max_chars=100)
    description = st.text_area("Description", height=100)

    is_binary = st.checkbox("Is Binary Habit (e.g. Did or Did Not?)", value=False)
    is_negative = st.checkbox("Is Negative Habit (e.g. Smoking)", value=False)

    freq_val = st.number_input("Target Frequency Value")
    freq_unit = st.text_input("Target Frequency Unit", max_chars=100)
    period_days = st.number_input("Target Period (in days)", min_value=1)

    submitted = st.form_submit_button("Create Habit")

    if submitted:
        if not name:
            st.warning("Name and Frequency Unit are required.")
        else:
            habit = db_ops.create_habit(
                name=name,
                description=description,
                is_binary_habit=is_binary,
                is_negative_habit=is_negative,
                target_frequency_value=freq_val,
                target_frequency_unit=freq_unit,
                target_period_in_days=int(period_days),
            )

            st.success(f"Habit '{habit.name}' created successfully!")

