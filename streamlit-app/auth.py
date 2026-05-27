"""
Authentication and authorization module for DXC Step Tracker.
Handles OAuth configuration, token management, and user authentication.
"""

import streamlit as st
import logging
from datetime import datetime
from requests_oauthlib import OAuth2Session
from db import supabase


# ------------------ OAUTH CONFIGURATION ------------------
def get_oauth_config():
    """Get OAuth configuration from secrets."""
    azure = st.secrets["azure"]
    return {
        "client_id": azure["client_id"],
        "client_secret": azure["client_secret"],
        "tenant_id": azure.get("tenant_id", "93f33571-550f-43cf-b09f-cd331338d086"),
        "authority": f"https://login.microsoftonline.com/{azure.get('tenant_id', '93f33571-550f-43cf-b09f-cd331338d086')}",
        "authorize_url": f"https://login.microsoftonline.com/{azure.get('tenant_id', '93f33571-550f-43cf-b09f-cd331338d086')}/oauth2/v2.0/authorize",
        "token_url": f"https://login.microsoftonline.com/{azure.get('tenant_id', '93f33571-550f-43cf-b09f-cd331338d086')}/oauth2/v2.0/token",
        "redirect_uri": "https://dxcsteptracker.streamlit.app/",
        "scopes": ["openid", "profile", "email", "User.Read", "Files.ReadWrite", "Files.ReadWrite.AppFolder"]
    }


def create_oauth_session():
    """Create and return an OAuth2Session with configured settings."""
    config = get_oauth_config()
    return OAuth2Session(
        client_id=config["client_id"],
        scope=config["scopes"],
        redirect_uri=config["redirect_uri"],
    )


# ------------------ SESSION MANAGEMENT ------------------
def initialize_session_state():
    """Initialize default session state values for authentication."""
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    if "display_name" not in st.session_state:
        st.session_state["display_name"] = ""
    if "user_email" not in st.session_state:
        st.session_state["user_email"] = ""


# ------------------ TOKEN VALIDATION ------------------
def is_token_expired(token):
    """Check if JWT token is expired."""
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get("exp")
        if exp:
            import time
            return time.time() >= exp
        return False
    except Exception:
        return True


def get_token_from_session():
    """Get access token from session state."""
    token = st.session_state.get("token")
    if token and "access_token" in token:
        return token["access_token"]
    return None


# ------------------ USER MANAGEMENT ------------------
def standardize_name(name):
    """Convert name from 'last, first' format to 'first last' format."""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name


def get_or_create_user(email, display_name):
    """Get existing user or create new user in database, return formatted name."""
    try:
        result = supabase.table("users").select("user_id, user_name").eq("user_email", email).execute()
        
        if result.data:
            return result.data[0]["user_name"]
        else:
            standardized_name = standardize_name(display_name)
            supabase.table("users").insert({
                "user_email": email,
                "user_name": standardized_name,
            }).execute()
            logging.info(f"New user created: {email[:3]}***@*** ({standardized_name})")
            return standardized_name
    except Exception as e:
        logging.error(f"Database error in get_or_create_user: {e}")
        return standardize_name(display_name)


def decode_token(token):
    """Decode JWT token and return user information."""
    try:
        import jwt
        token_to_decode = token.get("id_token") or token.get("access_token")
        if not token_to_decode:
            return None
        
        decoded = jwt.decode(token_to_decode, options={"verify_signature": False})
        return decoded
    except Exception as e:
        logging.error(f"Error decoding token: {e}")
        return None


def extract_user_info_from_token(decoded_token):
    """Extract user email and name from decoded token."""
    user_email = decoded_token.get("preferred_username") or decoded_token.get("email") or decoded_token.get("upn") or decoded_token.get("unique_name") or ""
    user_name_raw = decoded_token.get("name", "Unknown User")
    
    # Format name
    if "," in user_name_raw:
        last, first = [x.strip() for x in user_name_raw.split(",", 1)]
        user_name = f"{first} {last}"
    else:
        user_name = user_name_raw.strip()
    
    return user_email, user_name


# ------------------ OAUTH FLOW ------------------
def handle_oauth_redirect():
    """Handle OAuth redirect from Microsoft and exchange code for token."""
    query_params = st.query_params
    
    if "code" in query_params and st.session_state["token"] is None:
        try:
            config = get_oauth_config()
            oauth = create_oauth_session()
            
            token = oauth.fetch_token(
                token_url=config["token_url"],
                code=query_params["code"],
                client_id=config["client_id"],
                client_secret=config["client_secret"],
            )
            st.session_state["token"] = token
            st.query_params.clear()
            return True
        except Exception as e:
            error_str = str(e)
            logging.error(f"OAuth token fetch error: {error_str}")
            if "AADSTS70008" in error_str or "expired" in error_str.lower():
                st.error("Session timed out. Please log in again.")
            else:
                st.error(f"Authentication failed: {error_str[:200]}")
            return False
    return False


def process_login():
    """Process login flow: validate token, create user, set session state."""
    token = st.session_state.get("token")
    
    if not token:
        return False
    
    # Check if token is expired
    token_to_check = token.get("id_token") or token.get("access_token")
    if token_to_check and is_token_expired(token_to_check):
        return False
    
    # Decode token and get user info
    decoded = decode_token(token)
    if not decoded:
        return False
    
    user_email, user_name = extract_user_info_from_token(decoded)
    
    # Create or get user
    if not st.session_state.logged_in:
        username = get_or_create_user(user_email, user_name)
        st.session_state.logged_in = True
        st.session_state.username = user_email
        st.session_state.display_name = username
        st.session_state.user_email = user_email
        st.session_state.login_time = datetime.now().timestamp()
        logging.info(f"User logged in: {username} ({user_email[:3]}***@***)")
        return True
    
    return True


def get_login_url():
    """Generate OAuth authorization URL for login."""
    config = get_oauth_config()
    oauth = create_oauth_session()
    auth_url, _ = oauth.authorization_url(
        config["authorize_url"],
        prompt="select_account",
    )
    return auth_url


# ------------------ AUTHORIZATION ------------------
def is_admin(user_email: str) -> bool:
    """Check if a user email is in the admin list from secrets."""
    try:
        admin_emails = st.secrets.get("ADMIN_EMAILS", [])
        return user_email.lower() in [email.lower() for email in admin_emails]
    except Exception:
        return False


def require_admin():
    """Require admin access, stop execution if not admin."""
    user_email = st.session_state.get("user_email", "")
    if not is_admin(user_email):
        from components import log_audit_event
        log_audit_event("ADMIN_ACCESS_DENIED", user_email, "Attempted to access admin dashboard")
        st.error("Access denied.")
        st.stop()
