"""
Shared components and styling for the DXC Step Tracker application.
This module contains reusable functions for consistent theming across all pages.
"""
import streamlit as st
import pandas as pd
import bcrypt
import re
import os
import unicodedata
import logging
from pathlib import Path
from streamlit.components.v1 import html as st_html
from db import supabase
import string, random


def apply_dxc_theme():
    """Apply the DXC gradient theme and styling to the page."""
    st.markdown("""
    <style>
        /* White to Blue to Orange Gradient Background */
        .stApp {
            background: linear-gradient(135deg, 
                #FFFFFF 0%,     /* White */
                #F8FBFF 25%,    /* Light blue */
                #E3F2FD 50%,    /* Soft blue */
                #FFF3E0 75%,    /* Light orange */
                #FFE0B2 100%    /* Soft orange */
            );
            min-height: 100vh;
        }
        
        /* Make Streamlit header transparent */
        .stApp header {
            background: rgba(255, 255, 255, 0) !important;
            box-shadow: none !important;
            border: none !important;
        }
        
        .header-container {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
            color: white;
            padding: 20px 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .header-title { font-size: 42px; font-weight: bold; }
        .header-subtitle { font-size: 18px; margin-top: 5px; }
        
        /* Custom gradient buttons - exclude Logout and Submit */
        .stButton>button:not([kind="secondary"]) {
            background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
            color: white;
            border-radius: 8px;
            font-weight: bold;
            transition: 0.3s;
            border: none;
        }
        .stButton>button:not([kind="secondary"]):hover {
            background: linear-gradient(90deg, #6B94CB, #EF8A5C);
            transform: scale(1.05);
        }
        
        /* Secondary buttons and form submit buttons - white background, blue border */
        .stButton>button[kind="secondary"],
        .stFormSubmitButton>button {
            background-color: #FFFFFF !important;
            border: 1px solid #7BA4DB !important;
            color: #31333F !important;
            border-radius: 8px;
            font-weight: bold;
        }
        .stButton>button[kind="secondary"]:hover,
        .stFormSubmitButton>button:hover {
            background-color: #F8FBFF !important;
            border: 1px solid #6B94CB !important;
        }
        
        /* Sidebar border - creates visible divider */
        [data-testid="stSidebar"] {
            border-right: 2px solid #7BA4DB !important;
        }
        
        .footer-branding {
            text-align: center;
            font-size: 14px;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #7BA4DB;
        }
    </style>
    """, unsafe_allow_html=True)


def setup_logo(base_path=None):
    """
    Set up the DXC logo in the sidebar.
    
    Args:
        base_path: Path object pointing to the directory containing assets folder.
                  If None, assumes current file's parent directory.
    """
    if base_path is None:
        base_path = Path(__file__).parent
    
    logo_path = base_path / "assets" / "logo.png"
    
    if logo_path.exists():
        st.logo(str(logo_path), icon_image=str(logo_path), size="large")
    else:
        st.warning(f"⚠️ Logo not found at: {logo_path}")


def render_header(title, subtitle):
    """
    Render a styled header with title and subtitle.
    
    Args:
        title: Main header title
        subtitle: Subtitle text
    """
    st.markdown(f"""
    <div class="header-container">
        <div>
            <div class="header-title">{title}</div>
            <div class="header-subtitle">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the DXC Technology footer with blue divider."""
    st.markdown(
        "<div style='margin-top:60px; padding-top:20px; border-top:3px solid #7BA4DB;'></div>",
        unsafe_allow_html=True
    )


def render_sidebar_welcome(display_name=None):
    """
    Render welcome message in sidebar with logout button.
    Uses display_name from session state if not provided.
    
    Args:
        display_name: Display name to show (optional, defaults to session state)
        
    Returns:
        bool: True if logout button was clicked
    """
    if display_name is None:
        display_name = st.session_state.get("display_name", st.session_state.get("username", "User"))
    
    st.sidebar.markdown(
        f"<h3 style='color:#7BA4DB;'>Welcome, {display_name}!</h3>",
        unsafe_allow_html=True
    )
    return st.sidebar.button("Logout", type="secondary")


def hide_streamlit_branding():
    """Hide Streamlit's default branding elements."""
    st_html(
        """
        <script>
        window.addEventListener('load', () => {
            window.top.document.querySelectorAll(`[href*="streamlit.io"]`)
                .forEach(e => e.style.display = 'none');
        });
        </script>
        """,
        height=0,
    )


def check_login_required():
    """
    Check if user is logged in. If not, show warning and stop execution.
    
    Returns:
        str: Username if logged in, otherwise stops execution
    """
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()
    
    return st.session_state.get("username", "Guest")


def handle_logout():
    """Handle user logout by clearing session state and rerunning."""
    st.session_state.clear()
    st.rerun()


# ==================== UTILITY FUNCTIONS ====================

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        filename="app.log",
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def secure_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filenames to prevent directory traversal or injection.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "file"
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9.\-_]", "_", filename)
    return filename[:max_length]


def sanitize_username(username: str) -> str:
    """
    Sanitize and validate username.
    
    Args:
        username: Username to sanitize
        
    Returns:
        Sanitized username
        
    Raises:
        ValueError: If username doesn't meet requirements
    """
    username = username.strip()
    if not re.match(r"^[A-Za-z0-9 _.-]{3,50}$", username):
        raise ValueError(
            "Username must be 3–50 characters long and contain only letters, numbers, spaces, dots, underscores, or hyphens."
        )
    return username


def validate_password(password: str) -> bool:
    """
    Validate password strength.
    Requires at least 8 chars, one letter, one digit, one special char.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements, False otherwise
    """
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$', password))

# ==================== CHALLENGE FUNCTIONS ====================

def get_all_existing_codes(challenges: list[dict]) -> set[str]:
    """
    Collect all claim codes across all challenges.

    Returns:
        A set of codes (uppercased) for fast membership checks.
    """
    existing = set()
    for ch in challenges:
        for c in challenges[ch]["Codes"]:
            if isinstance(c, str):
                existing.add(c.strip().upper())
    return existing


def get_all_challenges():
    """
    Fetch all challenges from the Challenges.json file.
    
    Returns:
        List of challenge dicts, or empty list if file not found or invalid
    """
    try:
        challenges_path = Path(__file__).parent / "assets" / "Challenges.json"
        with open(challenges_path, "r") as f:
            import json
            return json.load(f)
    except Exception:
        return []


def generate_claim_code(challenges: list[dict], AlreadyGenerated: set[str], length: int = 8, max_attempts: int = 10_000) -> str:
    """
    Generate a random alphanumeric claim code that is unique across all challenges.

    Args:
        challenges: List of challenge dicts containing "Codes" lists
        AlreadyGenerated: Set of codes that have already been generated
        length: Length of the claim code (default 8)
        max_attempts: Safety cap to prevent infinite loops

    Returns:
        A unique randomly generated claim code

    Raises:
        RuntimeError: If a unique code cannot be found within max_attempts
        ValueError: If length is invalid
    """
    if length < 4:
        raise ValueError("length should be at least 4")
    
    characters = string.ascii_uppercase + string.digits
    existing_codes = get_all_existing_codes(challenges)

    for _ in range(max_attempts):
        claim_code = ''.join(random.choice(characters) for _ in range(length))
        if claim_code not in existing_codes and claim_code not in AlreadyGenerated:
            AlreadyGenerated.add(claim_code)
            return claim_code

    raise RuntimeError("Unable to generate a unique claim code — increase length or max_attempts.")

def validate_claim_code(challenges: list[dict], code: str, challenge_id: str) -> bool:
    """
    Validate a claim code against a specific challenge.
    
    Args:
        challenges: List of challenge dicts, each containing a "Codes" list
        code: The claim code to validate
        challenge_id: The ID of the specific challenge to validate against
    
    Returns:
        True if the code is valid for the specific challenge, False otherwise
    """
    for challenge in challenges:
        if challenges[challenge]["id"] == challenge_id:
            if code in challenges[challenge]["Codes"]:
                return True
            return False
    return False

# ==================== DATABASE FUNCTIONS ====================

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


# ==================== AUTHENTICATION FUNCTIONS ====================

def is_admin(user_email: str) -> bool:
    """
    Check if a user email is in the admin list from secrets.
    
    Args:
        user_email: User email to check
        
    Returns:
        True if user is an admin, False otherwise
    """
    try:
        admin_emails = st.secrets.get("ADMIN_EMAILS", [])
        return user_email.lower() in [email.lower() for email in admin_emails]
    except Exception:
        return False
