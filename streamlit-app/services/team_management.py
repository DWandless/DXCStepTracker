"""
Team management module for DXC Step Tracker.
Handles team creation, joining, leaving, and member performance tracking.
"""

import logging
from core.db import supabase


def get_user_team_id(user_id):
    """
    Get the team ID for a user.
    
    Args:
        user_id: User ID to check
        
    Returns:
        Team ID if user is in a team, None otherwise
    """
    try:
        user_data = supabase.table("users").select("team_id").eq("user_id", user_id).execute()
        return user_data.data[0].get("team_id") if user_data.data else None
    except Exception:
        return None


def get_team_info(team_id):
    """
    Get team information by team ID.
    
    Args:
        team_id: Team ID to fetch
        
    Returns:
        Team data dict or None if not found
    """
    try:
        team_info = supabase.table("teams").select("*").eq("team_id", team_id).execute()
        return team_info.data[0] if team_info.data else None
    except Exception:
        return None


def get_team_members(team_id):
    """
    Get all members of a team.
    
    Args:
        team_id: Team ID to fetch members for
        
    Returns:
        List of member dicts or empty list if not found
    """
    try:
        team_members = supabase.table("users").select("user_id, user_name").eq("team_id", team_id).execute()
        return team_members.data if team_members.data else []
    except Exception:
        return []


def get_team_leader_name(team_leader_id):
    """
    Get the name of a team leader.
    
    Args:
        team_leader_id: User ID of the team leader
        
    Returns:
        Leader name or "Unknown" if not found
    """
    try:
        leader_info = supabase.table("users").select("user_name").eq("user_id", team_leader_id).execute()
        return leader_info.data[0]['user_name'] if leader_info.data else "Unknown"
    except Exception:
        return "Unknown"


def get_member_performance(member_user_id):
    """
    Get performance statistics for a team member.
    
    Args:
        member_user_id: User ID of the member
        
    Returns:
        Dict with performance data or None if error
    """
    try:
        member_forms = supabase.table("forms").select("*").eq("user_id", member_user_id).execute()
        
        if member_forms.data:
            total_steps = sum(f['form_stepcount'] for f in member_forms.data)
            submission_count = len(member_forms.data)
            
            # Calculate average daily steps
            if submission_count > 0:
                avg_daily_steps = total_steps / submission_count
            else:
                avg_daily_steps = 0
            
            # Get last submission date
            from datetime import datetime
            sorted_forms = sorted(member_forms.data, key=lambda x: x['form_created_at'], reverse=True)
            last_submission = sorted_forms[0]['form_created_at'] if sorted_forms else "Never"
            
            # Calculate days since last submission
            if last_submission != "Never":
                try:
                    last_date = datetime.fromisoformat(last_submission)
                    days_since = (datetime.now() - last_date).days
                    last_submission_display = f"{last_date.strftime('%Y-%m-%d')} ({days_since} days ago)"
                except:
                    last_submission_display = last_submission
            else:
                last_submission_display = "Never"
            
            return {
                "total_steps": total_steps,
                "average_daily_steps": avg_daily_steps,
                "total_submissions": submission_count,
                "last_submission": last_submission_display
            }
        else:
            return {
                "total_steps": 0,
                "average_daily_steps": 0,
                "total_submissions": 0,
                "last_submission": "Never"
            }
    except Exception as e:
        logging.error(f"Error getting member performance: {e}")
        return None


def get_all_teams():
    """
    Get all teams from the database.
    
    Returns:
        List of team dicts or empty list if not found
    """
    try:
        all_teams = supabase.table("teams").select("*").execute()
        return all_teams.data if all_teams.data else []
    except Exception:
        return []


def get_available_teams(max_members=4):
    """
    Get teams that have space for new members.
    
    Args:
        max_members: Maximum members per team (default 4)
        
    Returns:
        List of team dicts with member count
    """
    try:
        all_teams = get_all_teams()
        available_teams = []
        
        for team in all_teams:
            members = supabase.table("users").select("user_id").eq("team_id", team["team_id"]).execute()
            member_count = len(members.data) if members.data else 0
            
            if member_count < max_members:
                team["member_count"] = member_count
                available_teams.append(team)
        
        return available_teams
    except Exception:
        return []


def is_user_team_leader(user_id):
    """
    Check if a user is a team leader.
    
    Args:
        user_id: User ID to check
        
    Returns:
        True if user is a team leader, False otherwise
    """
    try:
        is_leader = supabase.table("teams").select("team_id").eq("team_leader_id", user_id).execute()
        return len(is_leader.data) > 0 if is_leader.data else False
    except Exception:
        return False


def join_team(user_id, team_id):
    """
    Add a user to a team.
    
    Args:
        user_id: User ID to add to team
        team_id: Team ID to join
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        supabase.table("users").update({"team_id": team_id}).eq("user_id", user_id).execute()
        return True, None
    except Exception as e:
        logging.error(f"Error joining team: {e}")
        return False, str(e)


def leave_team(user_id):
    """
    Remove a user from their current team.
    
    Args:
        user_id: User ID to remove from team
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        supabase.table("users").update({"team_id": None}).eq("user_id", user_id).execute()
        return True, None
    except Exception as e:
        logging.error(f"Error leaving team: {e}")
        return False, str(e)


def create_team(team_name, team_leader_id):
    """
    Create a new team.
    
    Args:
        team_name: Name of the new team
        team_leader_id: User ID of the team leader
        
    Returns:
        tuple: (team_id, error_message)
    """
    try:
        result = supabase.table("teams").insert({
            "team_name": team_name,
            "team_leader_id": team_leader_id
        }).execute()
        
        if result.data:
            return result.data[0]["team_id"], None
        return None, "Failed to create team"
    except Exception as e:
        logging.error(f"Error creating team: {e}")
        return None, str(e)


def delete_team(team_id):
    """
    Delete a team and unassign all members.
    
    Args:
        team_id: Team ID to delete
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Unassign all team members
        supabase.table("users").update({"team_id": None}).eq("team_id", team_id).execute()
        # Delete the team
        supabase.table("teams").delete().eq("team_id", team_id).execute()
        return True, None
    except Exception as e:
        logging.error(f"Error deleting team: {e}")
        return False, str(e)
