import streamlit as st
import pandas as pd
from db import supabase
from pathlib import Path
from components import apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome, hide_streamlit_branding, check_login_required, handle_logout

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / ".streamlit" / "static" / "assets" / "logo.png"
st.set_page_config(page_title="Leaderboard", layout="wide", page_icon=logo_path2)

# Hide branding early
hide_streamlit_branding()

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("DXC Step Leaderboard", "Keep a Track of Leaders & Your Friends!")

# ------------------ SECURITY: LOGIN CHECK ------------------
username = check_login_required()

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome():
    handle_logout()

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["Individual Leaderboard", "Team Leaderboard"])

# ------------------ TAB 1: INDIVIDUAL LEADERBOARD ------------------
with tab1:
    st.subheader("Filter Leaderboard")

    col1, col2 = st.columns(2)
    with col1:
        selected_date = st.date_input(
            "Select a date (leave empty for all-time)",
            value=None,
            key="individual_date"
        )
    with col2:
        view_option = st.selectbox(
            "Show:",
            ["All", "Top 10", "Bottom 10"],
            key="individual_view"
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
    st.subheader("Individual Leaderboard")
    if selected_date:
        st.caption(f"Showing results for **{selected_date}**")
    else:
        st.caption("Showing **all-time** results")

    if leaderboard.empty:
        st.info("No data available to display.")
    else:
        st.dataframe(leaderboard, use_container_width=True)

        # Highlight top performer (only for All or Top 10 views)
        if view_option != "Bottom 10" and not leaderboard.empty:
            top_user = leaderboard.iloc[0]
            st.success(f"✪ {top_user['Username']} is leading with {int(top_user['Step Count'])} steps!")

# ------------------ TAB 2: TEAM LEADERBOARD ------------------
with tab2:
    st.subheader("Filter Team Leaderboard")
    
    col1, col2 = st.columns(2)
    with col1:
        team_selected_date = st.date_input(
            "Select a date (leave empty for all-time)",
            value=None,
            key="team_date"
        )
    with col2:
        team_view_option = st.selectbox(
            "Show:",
            ["All", "Top 10", "Bottom 10"],
            key="team_view"
        )
    
    # ------------------ FETCH TEAM DATA ------------------
    try:
        # Get all teams
        teams = supabase.table("teams").select("team_id, team_name").execute().data
        
        if not teams:
            st.info("No teams have been created yet.")
            st.stop()
        
        # Get all users with team assignments
        users_with_teams = supabase.table("users").select("user_id, team_id").execute().data
        
        # Get forms data
        forms_query = supabase.table("forms").select("user_id, form_stepcount, form_date")
        if team_selected_date:
            forms_query = forms_query.eq("form_date", str(team_selected_date))
        forms_data = forms_query.execute().data
        
        if not forms_data:
            st.info("No step data available for the selected date." if team_selected_date else "No step data available.")
            st.stop()
        
        # Create dataframes
        teams_df = pd.DataFrame(teams)
        users_teams_df = pd.DataFrame(users_with_teams)
        forms_df = pd.DataFrame(forms_data)
        
        # Merge forms with user team assignments
        merged = pd.merge(forms_df, users_teams_df, on="user_id", how="inner")
        
        # Filter out users without teams
        merged = merged[merged["team_id"].notna()]
        
        if merged.empty:
            st.info("No team members have submitted steps yet.")
            st.stop()
        
        # Aggregate steps by team
        team_steps = merged.groupby("team_id")["form_stepcount"].sum().reset_index()
        team_steps.rename(columns={"form_stepcount": "total_steps"}, inplace=True)
        
        # Merge with team names
        team_leaderboard = pd.merge(team_steps, teams_df, on="team_id", how="inner")
        
        # Get member count for each team
        member_counts = users_teams_df[users_teams_df["team_id"].notna()].groupby("team_id").size().reset_index(name="member_count")
        team_leaderboard = pd.merge(team_leaderboard, member_counts, on="team_id", how="left")
        team_leaderboard["member_count"] = team_leaderboard["member_count"].fillna(0).astype(int)
        
        # Select and rename columns
        team_leaderboard = team_leaderboard[["team_name", "total_steps", "member_count"]]
        team_leaderboard.rename(columns={
            "team_name": "Team Name",
            "total_steps": "Total Steps",
            "member_count": "Members"
        }, inplace=True)
        
        # ------------------ SORTING OPTIONS ------------------
        if team_view_option == "Top 10":
            team_leaderboard = team_leaderboard.sort_values("Total Steps", ascending=False).head(10)
        elif team_view_option == "Bottom 10":
            team_leaderboard = team_leaderboard.sort_values("Total Steps", ascending=True).head(10)
        else:  # All
            team_leaderboard = team_leaderboard.sort_values("Total Steps", ascending=False)
        
        team_leaderboard.reset_index(drop=True, inplace=True)
        team_leaderboard.index += 1  # Start rank from 1
        
        # ------------------ DISPLAY ------------------
        st.subheader("Team Leaderboard")
        if team_selected_date:
            st.caption(f"Showing results for **{team_selected_date}**")
        else:
            st.caption("Showing **all-time** results")
        
        if team_leaderboard.empty:
            st.info("No data available to display.")
        else:
            st.dataframe(team_leaderboard, use_container_width=True)
            
            # Highlight top team (only for All or Top 10 views)
            if team_view_option != "Bottom 10" and not team_leaderboard.empty:
                top_team = team_leaderboard.iloc[0]
                st.success(f"✪ {top_team['Team Name']} is leading with {int(top_team['Total Steps'])} steps!")
        
    except Exception as e:
        st.error(f"Error loading team leaderboard: {str(e)}")

# ------------------ FOOTER (ALWAYS RENDER) ------------------
render_footer()