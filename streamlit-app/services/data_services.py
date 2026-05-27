"""
Data services module for DXC Step Tracker.
Handles all database operations and data fetching.
"""

import pandas as pd
from db import supabase


def get_user_id(username: str):
    """
    Get user ID from username (email).
    
    Args:
        username: User email to look up
        
    Returns:
        User ID if found, None otherwise
    """
    try:
        res = supabase.table("users").select("user_id").eq("user_email", username).execute()
        if res.data:
            return res.data[0]["user_id"]
    except Exception:
        pass
    return None


def fetch_user_forms(user_id: int):
    """
    Fetch all forms for a specific user.
    
    Args:
        user_id: User ID to fetch forms for
        
    Returns:
        DataFrame of user forms, or empty DataFrame if none found
    """
    try:
        res = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_all_users():
    """
    Fetch all users from the database.
    
    Returns:
        List of user dictionaries, or empty list if none found
    """
    try:
        res = supabase.table("users").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_all_forms():
    """
    Fetch all forms from the database.
    
    Returns:
        List of form dictionaries, or empty list if none found
    """
    try:
        res = supabase.table("forms").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_all_teams():
    """
    Fetch all teams from the database.
    
    Returns:
        List of team dictionaries, or empty list if none found
    """
    try:
        res = supabase.table("teams").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_forms_by_user(user_id: int):
    """
    Fetch all forms for a specific user.
    
    Args:
        user_id: User ID to fetch forms for
        
    Returns:
        List of form dictionaries, or empty list if none found
    """
    try:
        res = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_unverified_high_step_submissions():
    """
    Fetch unverified submissions with step count > 20,000.
    
    Returns:
        DataFrame of submissions with user info, or empty DataFrame if none found
    """
    try:
        forms = supabase.table("forms") \
            .select("*") \
            .eq("form_verified", False) \
            .gt("form_stepcount", 19999) \
            .execute().data
        users = supabase.table("users").select("user_id, user_name").execute().data
        if not forms:
            return pd.DataFrame()
        df_forms = pd.DataFrame(forms)
        df_users = pd.DataFrame(users)
        return pd.merge(df_forms, df_users, on="user_id")
    except Exception:
        return pd.DataFrame()


def insert_form(form_data: dict):
    """
    Insert a new form into the database.
    
    Args:
        form_data: Dictionary containing form data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("forms").insert(form_data).execute()
        return True
    except Exception:
        return False


def update_form(form_id: str, update_data: dict):
    """
    Update an existing form in the database.
    
    Args:
        form_id: Form ID to update
        update_data: Dictionary containing fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("forms").update(update_data).eq("form_id", form_id).execute()
        return True
    except Exception:
        return False


def delete_form(form_id: str):
    """
    Delete a form from the database.
    
    Args:
        form_id: Form ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("forms").delete().eq("form_id", form_id).execute()
        return True
    except Exception:
        return False


def update_user_team(user_id: str, team_id: str = None):
    """
    Update a user's team assignment.
    
    Args:
        user_id: User ID to update
        team_id: Team ID to assign (None to unassign)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("users").update({"team_id": team_id}).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


def insert_team(team_data: dict):
    """
    Insert a new team into the database.
    
    Args:
        team_data: Dictionary containing team data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("teams").insert(team_data).execute()
        return True
    except Exception:
        return False


def delete_team(team_id: str):
    """
    Delete a team from the database.
    
    Args:
        team_id: Team ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("teams").delete().eq("team_id", team_id).execute()
        return True
    except Exception:
        return False
