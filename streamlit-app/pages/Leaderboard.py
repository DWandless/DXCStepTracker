import streamlit as st
from db import supabase
import pandas as pd

def render():
    st.set_page_config(page_title="Leaderboard", layout="wide")
    st.title("🏆 Step Leaderboard")

    # --- Date filter ---
    st.subheader("Filter Leaderboard")
    selected_date = st.date_input("Select a date to view daily leaderboard (or leave empty for all-time leaderboard)", value=None)

    # --- Fetch all form submissions ---
    forms_query = supabase.table("forms").select("user_id, form_stepcount, form_date")
    if selected_date:
        # Filter by the selected date
        forms_query = forms_query.eq("form_date", str(selected_date))
    
    forms = forms_query.execute().data

    if not forms:
        st.info("No step data available for the selected date." if selected_date else "No step data available.")
        return

    # --- Sum steps per user_id ---
    df = pd.DataFrame(forms)
    step_summary = df.groupby("user_id")["form_stepcount"].sum().reset_index()
    step_summary.rename(columns={"form_stepcount": "total_steps"}, inplace=True)

    # --- Get usernames from users table ---
    users = supabase.table("users").select("user_id, user_name").execute().data
    users_df = pd.DataFrame(users)

    # --- Merge step totals with usernames ---
    leaderboard = pd.merge(step_summary, users_df, on="user_id")
    leaderboard = leaderboard[["user_name", "total_steps"]]
    leaderboard.sort_values("total_steps", ascending=False, inplace=True)
    leaderboard.reset_index(drop=True, inplace=True)
    leaderboard.index += 1  # leaderboard position starts at 1

    # --- Display ---
    st.subheader("Leaderboard")
    if selected_date:
        st.caption(f"Showing results for **{selected_date}**")
    else:
        st.caption("Showing **all-time** results")

    st.dataframe(leaderboard, use_container_width=True)

# show logged-in user
if st.session_state.get("username"):
    st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")

render()