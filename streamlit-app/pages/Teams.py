import streamlit as st
import pandas as pd
import time
from pathlib import Path
from db import supabase
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, 
                        hide_streamlit_branding, check_login_required, render_sidebar_welcome, 
                        handle_logout, get_user_id)

# ------------------ PAGE CONFIG ------------------
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Teams", layout="wide", page_icon=logo_path)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("Team Management", "Join a team or create your own!")

# ------------------ LOGIN CHECK ------------------
username = check_login_required()
user_id = get_user_id(username)

# Debug: Show username and user_id
st.write(f"DEBUG - Logged in as: {username}, user_id: {user_id}")

if not user_id:
    st.error("User not found.")
    st.stop()

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome(username):
    handle_logout()

# ------------------ HELPER FUNCTIONS ------------------
def get_user_team_id(user_id):
    """Get the team_id for a user"""
    try:
        response = supabase.table("users").select("team_id").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0].get("team_id")
    except Exception:
        pass
    return None

def get_team_info(team_id):
    """Get team information"""
    try:
        response = supabase.table("teams").select("*").eq("team_id", team_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception:
        pass
    return None

def get_team_members(team_id):
    """Get all members of a team"""
    try:
        response = supabase.table("users").select("user_name").eq("team_id", team_id).execute()
        return response.data if response.data else []
    except Exception:
        return []

def get_team_member_count(team_id):
    """Get the number of members in a team"""
    members = get_team_members(team_id)
    return len(members)

def get_available_teams():
    """Get all teams that have less than 4 members"""
    try:
        all_teams = supabase.table("teams").select("*").execute().data
        if not all_teams:
            return []
        
        available = []
        for team in all_teams:
            member_count = get_team_member_count(team["team_id"])
            if member_count < 4:
                team["member_count"] = member_count
                available.append(team)
        
        return available
    except Exception:
        return []

def create_team(team_name, team_leader_username, user_id):
    """Create a new team and assign the creator as team leader"""
    try:
        # Create the team
        team_response = supabase.table("teams").insert({
            "team_name": team_name,
            "team_leader": team_leader_username
        }).execute()
        
        if team_response.data and len(team_response.data) > 0:
            team_id = team_response.data[0]["team_id"]
            
            # Assign the user to the team
            update_response = supabase.table("users").update({
                "team_id": team_id
            }).eq("user_id", user_id).execute()
            
            # Verify the update was successful
            if update_response.data and len(update_response.data) > 0:
                return True, team_id
            else:
                # Rollback: delete the team if user assignment failed
                supabase.table("teams").delete().eq("team_id", team_id).execute()
                st.error("Failed to assign you to the team. Please try again.")
                return False, None
            
        return False, None
    except Exception as e:
        st.error(f"Error creating team: {str(e)}")
        return False, None

def join_team(team_id, user_id):
    """Join an existing team"""
    try:
        # Check if team is full
        if get_team_member_count(team_id) >= 4:
            return False, "Team is full (maximum 4 members)"
        
        # Debug: Check what we're trying to update
        st.write(f"DEBUG - Attempting to join team_id: {team_id} for user_id: {user_id}")
        
        # Assign user to team
        update_response = supabase.table("users").update({
            "team_id": team_id
        }).eq("user_id", user_id).execute()
        
        # Debug: Check the response
        st.write(f"DEBUG - Update response data: {update_response.data}")
        
        # Verify the update worked
        if update_response.data and len(update_response.data) > 0:
            return True, "Successfully joined team!"
        else:
            return False, "Failed to update your team assignment. Please try again."
    except Exception as e:
        st.error(f"Exception details: {str(e)}")
        return False, f"Error joining team: {str(e)}"

def leave_team(user_id):
    """Leave current team"""
    try:
        supabase.table("users").update({
            "team_id": None
        }).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False

# ------------------ MAIN CONTENT ------------------
# Force refresh of user's team status
current_team_id = get_user_team_id(user_id)

# Debug: Show current team_id (remove this after testing)
st.write(f"Debug - Current team_id: {current_team_id}, user_id: {user_id}")

if current_team_id:
    # User is already in a team - show team info
    team_info = get_team_info(current_team_id)
    team_members = get_team_members(current_team_id)
    
    if team_info:
        st.success(f"You are a member of **{team_info['team_name']}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Team Information")
            st.markdown(f"**Team Name:** {team_info['team_name']}")
            st.markdown(f"**Team Leader:** {team_info['team_leader']}")
            st.markdown(f"**Members:** {len(team_members)}/4")
        
        with col2:
            st.subheader("Team Members")
            for member in team_members:
                st.markdown(f"- {member['user_name']}")
        
        st.markdown("---")
        
        # Leave team button
        if st.button("Leave Team", type="secondary"):
            if leave_team(user_id):
                st.success("You have left the team.")
                st.rerun()
            else:
                st.error("Error leaving team. Please try again.")
    else:
        st.error("Error loading team information.")

else:
    # User is not in a team - show options to join or create
    st.info("You are not currently part of a team. Join an existing team or create your own!")
    
    tab1, tab2 = st.tabs(["Join a Team", "Create a Team"])
    
    # ------------------ TAB 1: JOIN TEAM ------------------
    with tab1:
        st.subheader("Available Teams")
        
        available_teams = get_available_teams()
        
        if available_teams:
            for team in available_teams:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"### {team['team_name']}")
                        st.caption(f"Leader: {team['team_leader']}")
                    
                    with col2:
                        st.metric("Members", f"{team['member_count']}/4")
                    
                    with col3:
                        if st.button("Join", key=f"join_{team['team_id']}", type="secondary"):
                            success, message = join_team(team['team_id'], user_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    
                    st.markdown("---")
        else:
            st.info("No teams available to join. Create your own team below!")
    
    # ------------------ TAB 2: CREATE TEAM ------------------
    with tab2:
        st.subheader("Create Your Team")
        st.write("As team leader, you'll be able to manage your team and invite members.")
        
        with st.form("create_team_form"):
            team_name = st.text_input(
                "Team Name",
                max_chars=50,
                help="Choose a unique name for your team (max 50 characters)"
            )
            
            submitted = st.form_submit_button("Create Team", type="secondary")
            
            if submitted:
                if not team_name or len(team_name.strip()) == 0:
                    st.error("Please enter a team name.")
                elif len(team_name) < 3:
                    st.error("Team name must be at least 3 characters long.")
                else:
                    # Check if team name already exists
                    existing = supabase.table("teams").select("team_name").eq("team_name", team_name.strip()).execute()
                    if existing.data and len(existing.data) > 0:
                        st.error("A team with this name already exists. Please choose a different name.")
                    else:
                        success, team_id = create_team(team_name.strip(), username, user_id)
                        if success:
                            st.success(f"Team '{team_name}' created successfully! You are now the team leader.")
                            st.balloons()
                            # Small delay to ensure database commit
                            time.sleep(0.5)
                            # Clear any cached data
                            if 'team_created' in st.session_state:
                                del st.session_state['team_created']
                            st.rerun()
                        else:
                            st.error("Error creating team. Please try again.")

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()
