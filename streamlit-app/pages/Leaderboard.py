import streamlit as st
import pandas as pd
from db import supabase
from pathlib import Path
from components import apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome, hide_streamlit_branding, check_login_required, handle_logout

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Leaderboard", layout="wide", page_icon=logo_path2)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("DXC Step Leaderboard", "Track the leaders and keep moving!")

# ------------------ SECURITY: LOGIN CHECK ------------------
username = check_login_required()

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
try:
    forms_query = supabase.table("forms").select("user_id, form_stepcount, form_date")
    if selected_date:
        forms_query = forms_query.eq("form_date", str(selected_date))
    forms = forms_query.execute().data
except Exception as e:
    st.error(f"Database error while fetching forms: {e}")
    st.stop()

if not forms:
    st.info("No step data available for the selected date." if selected_date else "No step data available.")
    st.stop()

df = pd.DataFrame(forms)

# ------------------ AGGREGATE STEPS SECURELY ------------------
try:
    step_summary = df.groupby("user_id")["form_stepcount"].sum().reset_index()
    step_summary.rename(columns={"form_stepcount": "total_steps"}, inplace=True)
except Exception as e:
    st.error(f"Error processing step data: {e}")
    st.stop()

# ------------------ GET USERNAMES ------------------
try:
    users = supabase.table("users").select("user_id, user_name").execute().data
    users_df = pd.DataFrame(users)
except Exception as e:
    st.error(f"Error fetching user data, please try again later.")
    st.stop()

# Merge steps with usernames
leaderboard = pd.merge(step_summary, users_df, on="user_id", how="inner")
leaderboard = leaderboard[["user_name", "total_steps"]]


leaderboard.rename(columns={
    "user_name": "Username",
    "total_steps": "Step Count"
}, inplace=True)

# ------------------ SORTING OPTIONS ------------------
if view_option == "Top 10":
    leaderboard = leaderboard.sort_values("Step Count", ascending=False).head(10)
elif view_option == "Bottom 10":
    leaderboard = leaderboard.sort_values("Step Count", ascending=True).head(10)
else:  # All
    leaderboard = leaderboard.sort_values("Step Count", ascending=False)

leaderboard.reset_index(drop=True, inplace=True)
leaderboard.index += 1  # Start rank from 1

# ------------------ DISPLAY ------------------
st.subheader("Leaderboard")
if selected_date:
    st.caption(f"Showing results for **{selected_date}**")
else:
    st.caption("Showing **all-time** results")

if leaderboard.empty:
    st.info("No data available to display.")
else:
    st.dataframe(leaderboard, width="stretch")

    # Highlight top performer (only for All or Top 10 views)
    if view_option != "Bottom 10" and not leaderboard.empty:
        top_user = leaderboard.iloc[0]
        st.success(f"🥇 {top_user['Username']} is leading with {int(top_user['Step Count'])} steps!")

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome(username):
    handle_logout()

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()