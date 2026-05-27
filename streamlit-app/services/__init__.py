"""Business logic and data services modules."""

# Import directly from modules to avoid circular imports
import pandas as pd
from core.db import supabase


def get_user_id(username: str):
    """Get user ID from username (email)."""
    try:
        res = supabase.table("users").select("user_id").eq("user_email", username).execute()
        if res.data:
            return res.data[0]["user_id"]
    except Exception:
        pass
    return None


def fetch_user_forms(user_id: int):
    """Fetch all forms for a specific user."""
    try:
        res = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def fetch_all_users():
    """Fetch all users from the database."""
    try:
        res = supabase.table("users").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_all_forms():
    """Fetch all forms from the database."""
    try:
        res = supabase.table("forms").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_all_teams():
    """Fetch all teams from the database."""
    try:
        res = supabase.table("teams").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


def fetch_unverified_high_step_submissions():
    """Fetch unverified submissions with step count > 20,000."""
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


def delete_form(form_id: str):
    """Delete a form from the database."""
    try:
        supabase.table("forms").delete().eq("form_id", form_id).execute()
        return True
    except Exception:
        return False


def update_form(form_id: str, update_data: dict):
    """Update an existing form in the database."""
    try:
        supabase.table("forms").update(update_data).eq("form_id", form_id).execute()
        return True
    except Exception:
        return False


# Import from submodules
from .step_submission import (
    validate_step_submission, check_submission_cooldown, check_daily_submission_limit,
    process_screenshot_upload, submit_step_form, get_last_submission_time
)
from .team_management import (
    get_user_team_id, get_team_info, get_team_members, get_team_leader_name,
    get_member_performance, get_all_teams, get_available_teams, is_user_team_leader,
    join_team, leave_team, create_team, delete_team
)
from .challenges import (
    get_all_challenges, get_all_existing_codes, generate_claim_code,
    hash_claim_code, validate_claim_code, save_claim_codes_to_file
)

__all__ = [
    'get_user_id', 'fetch_user_forms', 'fetch_all_users', 'fetch_all_forms',
    'fetch_all_teams', 'fetch_unverified_high_step_submissions',
    'delete_form', 'update_form',
    'validate_step_submission', 'check_submission_cooldown', 'check_daily_submission_limit',
    'process_screenshot_upload', 'submit_step_form', 'get_last_submission_time',
    'get_user_team_id', 'get_team_info', 'get_team_members', 'get_team_leader_name',
    'get_member_performance', 'get_all_teams', 'get_available_teams', 'is_user_team_leader',
    'join_team', 'leave_team', 'create_team', 'delete_team',
    'get_all_challenges', 'get_all_existing_codes', 'generate_claim_code',
    'hash_claim_code', 'validate_claim_code', 'save_claim_codes_to_file'
]
