"""
Shared components and styling for the DXC Step Tracker application.
This module contains reusable functions for consistent theming across all pages.
"""

import streamlit as st
import logging
import os
import re
import unicodedata
import base64
import html
import pandas as pd
from datetime import datetime
from pathlib import Path
from db import supabase
from streamlit.components.v1 import html as st_html

# -------------------------------------------------------------------
# Paths + Static Assets
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / ".streamlit" / "static" / "assets"

LOGO_PATH = ASSETS_DIR / "logo.png"
HEADER_FONT_PATH = ASSETS_DIR / "GT-Standard-L-Extended-Medium.otf"


def apply_header_font():
    """Apply the GT-Standard font to headers using base64 encoding."""
    if not HEADER_FONT_PATH.exists():
        return

    try:
        font_b64 = base64.b64encode(HEADER_FONT_PATH.read_bytes()).decode("utf-8")
    except Exception:
        return

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'GTStandardHeader';
            src: url(data:font/otf;base64,{font_b64}) format('opentype');
            font-weight: 500;
            font-style: normal;
        }}

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6,
        .header-title, .header-subtitle {{
            font-family: 'GTStandardHeader', sans-serif !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_dxc_theme():
    """Apply the DXC gradient theme and styling to the page."""
    apply_header_font()
    
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


def setup_logo():
    """Setup the logo in the sidebar."""
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), icon_image=str(LOGO_PATH), size="large")
    else:
        st.warning(f"Logo not found at: {LOGO_PATH}")


def render_header(title: str, subtitle: str):
    """
    Render the DXC Technology header with blue gradient background.
    
    Args:
        title: Main header title
        subtitle: Subtitle text
    """
    # Escape user-generated content to prevent XSS
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    
    st.markdown(
        f"""
        <div class="header-container">
            <div>
                <div class="header-title">{safe_title}</div>
                <div class="header-subtitle">{safe_subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


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
    
    # Escape user-generated content to prevent XSS
    safe_display_name = html.escape(display_name)
    
    st.sidebar.markdown(
        f"<h3 style='color:#7BA4DB;'>Welcome, {safe_display_name}!</h3>",
        unsafe_allow_html=True
    )
    return st.sidebar.button("Logout", type="secondary")


def hide_streamlit_branding():
    """Hide Streamlit's default branding elements."""
    st.components.v1.html(
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
    
    # Check session timeout (8 hours)
    login_time = st.session_state.get("login_time")
    if login_time:
        session_timeout = 8 * 3600  # 8 hours in seconds
        if datetime.now().timestamp() - login_time > session_timeout:
            st.warning("Session expired. Please log in again.")
            handle_logout()
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


def log_audit_event(event_type, user_email, details=None):
    """
    Log audit events for sensitive operations.
    
    Args:
        event_type: Type of event (e.g., "VERIFICATION", "CODE_GENERATION", "ADMIN_ACCESS")
        user_email: Email of the user performing the action
        details: Additional details about the event (optional)
    """
    try:
        # Sanitize email for logging
        safe_email = user_email[:3] + "***@***" if user_email else "unknown"
        
        log_message = f"AUDIT: {event_type} - User: {safe_email}"
        if details:
            log_message += f" - Details: {details}"
        
        logging.info(log_message)
    except Exception as e:
        logging.error(f"Failed to log audit event: {e}")


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
        challenges_path = Path(__file__).parent / ".streamlit" / "static" / "assets" / "Challenges.json"
        if not challenges_path.exists():
            logging.error(f"Challenges.json not found at: {challenges_path}")
            return []
        with open(challenges_path, "r") as f:
            challenges = json.load(f)
            logging.info(f"Loaded {len(challenges)} challenges")
            return challenges
    except Exception as e:
        logging.error(f"Error loading challenges: {e}")
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

def hash_claim_code(code: str) -> str:
    """
    Hash a claim code using SHA256 for secure storage.
    
    Args:
        code: The plain text claim code to hash
    
    Returns:
        The SHA256 hash of the code as a hexadecimal string
    """
    return hashlib.sha256(code.encode()).hexdigest()


def validate_claim_code(challenges: list[dict], code: str, challenge_id: str) -> bool:
    """
    Validate a claim code against a specific challenge by comparing hashes.
    
    Args:
        challenges: List of challenge dicts, each containing a "Codes" list
        code: The claim code to validate
        challenge_id: The ID of the specific challenge to validate against
    
    Returns:
        True if the code is valid for the specific challenge, False otherwise
    """
    code_hash = hash_claim_code(code)
    for challenge in challenges:
        if str(challenges[challenge]["id"]) == str(challenge_id):
            if code_hash in challenges[challenge]["Codes"]:
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
