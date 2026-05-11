import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from PIL import Image, UnidentifiedImageError
import re, unicodedata, random, io
from pathlib import Path
from db import supabase
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, hide_streamlit_branding,
                        secure_filename, get_user_id, fetch_user_forms, render_sidebar_welcome, handle_logout)

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parent / "assets" / "logo.png"
st.set_page_config(page_title="DXC Step Tracker", layout="wide", page_icon=logo_path2)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo()
render_header("DXC Step Tracker", "Keep Moving and Track your steps below!")

# ------------------ HELPERS ------------------
# Utility functions now imported from components

def get_last_submission_time(user_id):
    try:
        response = (
            supabase.table("forms")
            .select("form_created_at")
            .eq("user_id", user_id)
            .order("form_created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) == 1:
            return datetime.fromisoformat(response.data[0]["form_created_at"])
    except Exception:
        pass
    return None

# ------------------ LOGIN CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username")  # This is the email
user_id = get_user_id(username)
if not user_id:
    st.error("User not found.")
    st.stop()

if render_sidebar_welcome():
    handle_logout()

# ------------------ TABS ------------------
tab1, tab2, tab3 = st.tabs(["✚ Submit Steps", "➜ Daily Progress", "⚑ Teams"])

# ------------------ TAB 1: SUBMIT STEPS ------------------
with tab1:
    st.header("✚ Submit Your Steps")
    date_col, step_col = st.columns(2)
    with date_col: 
        step_date = st.date_input(
            "Date",
            help="Select the date when you recorded these steps. You can submit steps for past dates."
        )
    with step_col: 
        steps = st.number_input(
            "Step Count", 
            min_value=0, 
            step=100,
            help="Enter the total number of steps you walked on this date (1-100,000)."
        )
    screenshot = st.file_uploader(
        "Upload Screenshot (PNG/JPG)", 
        type=["png", "jpg", "jpeg"],
        help="Upload a screenshot from your fitness tracker or step counter app as proof of your steps. Required for all submissions."
    )

    if screenshot:
        if screenshot.size > MAX_UPLOAD_SIZE:
            st.error("File too large. Max 5 MB."); st.stop()
        try:
            img = Image.open(screenshot)
            img.thumbnail((600, 600))
            st.image(img, caption="Preview", width=300)
        except UnidentifiedImageError:
            st.error("Invalid image."); st.stop()

    if st.button("Submit", type="secondary"):
        now = datetime.now()
        last_submission = st.session_state.get("last_submission_time") or get_last_submission_time(user_id)

        # --- 1-minute cooldown check ---
        if last_submission and now - last_submission < timedelta(seconds=60): # Brian wicks wanted this changed :)
            remaining = timedelta(seconds=60) - (now - last_submission)
            minutes, seconds = divmod(remaining.total_seconds(), 60)
            st.warning(f"Please wait {int(seconds)}s before submitting again.")
        elif steps <= 0 or steps > 100000:
            st.error("Enter a valid step count (1–100,000).")
        elif not screenshot:
            st.error("Please upload a screenshot.")
        else:
            try:
                img = Image.open(screenshot).convert("RGB")
                filename = secure_filename(f"{safe_username}_{step_date}_{datetime.now().strftime('%H%M%S')}.jpg")
                path = os.path.join(UPLOAD_FOLDER, filename)
                img.save(path, format="JPEG", quality=85, optimize=True)
                supabase.table("forms").insert({
                    "form_filepath": filename,
                    "form_stepcount": steps,
                    "form_date": str(step_date),
                    "user_id": user_id,
                    "form_verified": False
                }).execute()

                # Delete the image if steps are under 10,000 (not required for verification)
                if steps < 20000:
                    try:
                        os.remove(path)
                    except FileNotFoundError:
                        pass

                # Record new submission time
                st.session_state.last_submission_time = now

                st.success("✔ Step count submitted successfully!")
            except Exception as e:
                st.error("Error processing upload.")
                st.exception(e)

# ------------------ TAB 2: DAILY PROGRESS ------------------
with tab2:
    st.header("➜ Daily Progress")
    df = fetch_user_forms(user_id)

    if df.empty:
        st.info("No submissions yet.")
    else:
        df["form_date"] = pd.to_datetime(df["form_date"]).dt.date
        daily_steps = df.groupby("form_date")["form_stepcount"].sum().reset_index()
        total_steps = int(df["form_stepcount"].sum())
        today_steps = int(daily_steps[daily_steps["form_date"] == datetime.now().date()]["form_stepcount"].sum())
        days_participated = len(daily_steps)
        avg_steps = int(daily_steps["form_stepcount"].mean())
        distance_km = round(total_steps * 0.0008, 2)
        calories = int(total_steps * 0.04)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Steps", total_steps)
        c2.metric("Steps Today", today_steps)
        c3.metric("Days Participated", days_participated)

        c4, c5, c6 = st.columns(3)
        c4.metric("Avg Daily Steps", avg_steps)
        c5.metric("Total Distance (km)", distance_km)
        c6.metric("Total Calories Burned", calories)

        # --- Streak ---
        sorted_dates = sorted(daily_steps["form_date"])
        streak = 0
        if sorted_dates:
            streak = 1
            for i in range(len(sorted_dates) - 1, 0, -1):
                if (sorted_dates[i] - sorted_dates[i - 1]) == timedelta(days=1):
                    streak += 1
                else:
                    break
            if sorted_dates[-1] != datetime.now().date():
                streak = 0
        st.success(f"🗲 Current Streak: {streak} days" if streak else "No active streak.")

        # --- Graph ---
        fig = px.bar(
            daily_steps,
            x="form_date",
            y="form_stepcount",
            title=f"{safe_username}'s Steps per Day",
            color_discrete_sequence=["#7BA4DB"],
            labels={"form_date": "Date", "form_stepcount": "Step Count"},
            template="plotly_white"
        )
        fig.update_xaxes(tickformat="%Y-%m-%d")
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

# ------------------ TAB 3: TEAMS ------------------
with tab3:
    st.header("⚑ Team Management")
    
    # Get user's current team
    try:
        user_data = supabase.table("users").select("team_id").eq("user_id", user_id).execute()
        current_team_id = user_data.data[0].get("team_id") if user_data.data else None
    except Exception:
        current_team_id = None
    
    if current_team_id:
        # User is in a team - show team info
        try:
            team_info = supabase.table("teams").select("*").eq("team_id", current_team_id).execute()
            team_members = supabase.table("users").select("user_name").eq("team_id", current_team_id).execute()
            
            if team_info.data:
                team = team_info.data[0]
                
                st.subheader("Team Information")
                st.markdown(f"**Team Name:** {team['team_name']}")
                st.markdown(f"**Team Leader:** {team['team_leader']}")
                
                with st.expander(f"View Members ({len(team_members.data)}/4)", expanded=False):
                    for member in team_members.data:
                        st.markdown(f"• {member['user_name']}")
                
                st.markdown("---")
                
                # Check if current user is the team leader
                is_team_leader = (username == team['team_leader'])
                
                if is_team_leader:
                    # Team leader can delete the team
                    if st.button("Delete Team", type="secondary", key="delete_team_btn"):
                        try:
                            # Unassign all team members
                            supabase.table("users").update({"team_id": None}).eq("team_id", current_team_id).execute()
                            # Delete the team
                            supabase.table("teams").delete().eq("team_id", current_team_id).execute()
                            st.success("Team deleted successfully. All members have been unassigned.")
                            st.rerun()
                        except Exception:
                            st.error("Error deleting team. Please try again.")
                else:
                    # Regular members can leave the team
                    if st.button("Leave Team", type="secondary", key="leave_team_btn"):
                        try:
                            supabase.table("users").update({"team_id": None}).eq("user_id", user_id).execute()
                            st.success("You have left the team.")
                            st.rerun()
                        except Exception:
                            st.error("Error leaving team. Please try again.")
        except Exception:
            st.error("Error loading team information.")
    else:
        # User is not in a team
        # Check if user is already a team leader
        try:
            is_leader = supabase.table("teams").select("team_id").eq("team_leader", username).execute()
            user_is_leader = len(is_leader.data) > 0 if is_leader.data else False
        except Exception:
            user_is_leader = False
        
        # Show tabs based on whether user is a team leader
        if user_is_leader:
            # User is a team leader but not in a team - only show join option
            st.warning("You already created a team. You can only join existing teams.")
            
            st.subheader("Available Teams")
            try:
                all_teams = supabase.table("teams").select("*").execute()
                
                if all_teams.data:
                    available_teams = []
                    for team in all_teams.data:
                        members = supabase.table("users").select("user_id").eq("team_id", team["team_id"]).execute()
                        member_count = len(members.data) if members.data else 0
                        
                        if member_count < 4:
                            team["member_count"] = member_count
                            available_teams.append(team)
                    
                    if available_teams:
                        for team in available_teams:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"### {team['team_name']}")
                                st.caption(f"Leader: {team['team_leader']}")
                            
                            with col2:
                                st.metric("Members", f"{team['member_count']}/4")
                            
                            with col3:
                                if st.button("Join", key=f"join_leader_{team['team_id']}", type="secondary"):
                                    try:
                                        supabase.table("users").update({"team_id": team['team_id']}).eq("user_id", user_id).execute()
                                        st.success("Successfully joined team!")
                                        st.rerun()
                                    except Exception:
                                        st.error("Error joining team.")
                            
                            st.markdown("---")
                    else:
                        st.info("No teams available to join.")
                else:
                    st.info("No teams exist yet.")
            except Exception:
                st.error("Error loading teams.")
        else:
            # User is not a team leader - show both tabs
            subtab1, subtab2 = st.tabs(["Join a Team", "Create a Team"])
            
            with subtab1:
                st.subheader("Available Teams")
                try:
                    all_teams = supabase.table("teams").select("*").execute()
                    
                    if all_teams.data:
                        available_teams = []
                        for team in all_teams.data:
                            members = supabase.table("users").select("user_id").eq("team_id", team["team_id"]).execute()
                            member_count = len(members.data) if members.data else 0
                            
                            if member_count < 4:
                                team["member_count"] = member_count
                                available_teams.append(team)
                        
                        if available_teams:
                            for team in available_teams:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                
                                with col1:
                                    st.markdown(f"### {team['team_name']}")
                                    st.caption(f"Leader: {team['team_leader']}")
                                
                                with col2:
                                    st.metric("Members", f"{team['member_count']}/4")
                                
                                with col3:
                                    if st.button("Join", key=f"join_{team['team_id']}", type="secondary"):
                                        try:
                                            supabase.table("users").update({"team_id": team['team_id']}).eq("user_id", user_id).execute()
                                            st.success("Successfully joined team!")
                                            st.rerun()
                                        except Exception:
                                            st.error("Error joining team.")
                                
                                st.markdown("---")
                        else:
                            st.info("No teams available to join.")
                    else:
                        st.info("No teams exist yet. Be the first to create one!")
                except Exception:
                    st.error("Error loading teams.")
            
            with subtab2:
                st.subheader("Create Your Team")
                st.write("As team leader, you'll manage your team.")
                
                with st.form("create_team_form"):
                    team_name = st.text_input(
                        "Team Name",
                        max_chars=50,
                        help="Choose a unique name for your team (max 50 characters)"
                    )
                    
                    submitted = st.form_submit_button("Create Team", type="secondary")
                    
                    if submitted:
                        if not team_name or len(team_name.strip()) < 3:
                            st.error("Team name must be at least 3 characters long.")
                        else:
                            try:
                                existing = supabase.table("teams").select("team_name").eq("team_name", team_name.strip()).execute()
                                
                                if existing.data:
                                    st.error("A team with this name already exists.")
                                else:
                                    team_response = supabase.table("teams").insert({
                                        "team_name": team_name.strip(),
                                        "team_leader": username
                                    }).execute()
                                    
                                    if team_response.data:
                                        new_team_id = team_response.data[0]["team_id"]
                                        supabase.table("users").update({"team_id": new_team_id}).eq("user_id", user_id).execute()
                                        
                                        st.success(f"Team '{team_name}' created successfully!")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error("Error creating team.")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()
