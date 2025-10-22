import streamlit as st
import pandas as pd
from db import supabase

# ------------------ CONFIG ------------------
st.set_page_config(page_title="🏆 Leaderboard", layout="wide")
st.title("🏆 Movember Step Leaderboard")
st.write("Welcome to the Movember Step Tracker! Below is the leaderboard for the challenge.")

# ------------------ LOGIN CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username", "Guest")

# ------------------ FILTERS ------------------
st.subheader("Filter Leaderboard")

col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input(
        "Select a date (leave empty for all-time)",
        value=None
    )
with col2:
    view_option = st.selectbox(
        "Show:",
        ["All", "Top 10", "Bottom 10"]
    )

# ------------------ FETCH DATA FROM SUPABASE ------------------
forms_query = supabase.table("forms").select("user_id, form_stepcount, form_date")
if selected_date:
    forms_query = forms_query.eq("form_date", str(selected_date))

forms = forms_query.execute().data

if not forms:
    st.info("No step data available for the selected date." if selected_date else "No step data available.")
    st.stop()

df = pd.DataFrame(forms)

# ------------------ AGGREGATE STEPS ------------------
step_summary = df.groupby("user_id")["form_stepcount"].sum().reset_index()
step_summary.rename(columns={"form_stepcount": "total_steps"}, inplace=True)

# ------------------ GET USERNAMES ------------------
users = supabase.table("users").select("user_id, user_name").execute().data
users_df = pd.DataFrame(users)

# Merge steps with usernames
leaderboard = pd.merge(step_summary, users_df, on="user_id")
leaderboard = leaderboard[["user_name", "total_steps"]]

# Apply sorting logic based on slicer
if view_option == "Top 10":
    leaderboard = leaderboard.sort_values("total_steps", ascending=False).head(10)
elif view_option == "Bottom 10":
    leaderboard = leaderboard.sort_values("total_steps", ascending=True).head(10)
else:  # All
    leaderboard = leaderboard.sort_values("total_steps", ascending=False)

leaderboard.reset_index(drop=True, inplace=True)
leaderboard.index += 1  # Start rank from 1

# ------------------ DISPLAY ------------------
st.subheader("Leaderboard")
if selected_date:
    st.caption(f"Showing results for **{selected_date}**")
else:
    st.caption("Showing **all-time** results")

st.dataframe(leaderboard, width="stretch")

# Highlight top user (only if showing all or top 10)
if not leaderboard.empty and view_option != "Bottom 10":
    top_user = leaderboard.iloc[0]
    st.success(f"🥇 {top_user['user_name']} is leading with {int(top_user['total_steps'])} steps!")

# ------------------ SIDEBAR USER INFO ------------------
if username:
    st.sidebar.markdown(f"**User:** {username}")