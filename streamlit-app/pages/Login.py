import streamlit as st
import logging
from db import supabase
from pathlib import Path
from authlib.integrations.requests_client import OAuth2Session
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome,
                        hide_streamlit_branding, setup_logging)

# ------------------ CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Login", layout="wide", page_icon=logo_path2)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("DXC Step Tracker", "Log in to start tracking your steps!")

# ------------------ LOGGING ------------------
setup_logging()

# ------------------ AZURE OAUTH CONFIG ------------------
azure = st.secrets["azure"]
CLIENT_ID = azure["client_id"]
CLIENT_SECRET = azure["client_secret"]
TENANT_ID = "93f33571-550f-43cf-b09f-cd331338d086"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_URL = f"{AUTHORITY}/oauth2/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/token"
REDIRECT_URI = "https://dxcsteptracker.streamlit.app/Login"

# Use v1.0 OAuth with resource parameter (doesn't require Graph API permissions)
oauth = OAuth2Session(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope=["openid"],  # Minimal scope for v1.0
    redirect_uri=REDIRECT_URI,
)

# ------------------ SESSION DEFAULTS ------------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""  # Will store email
if "display_name" not in st.session_state:
    st.session_state["display_name"] = ""  # Will store formatted name
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

# ------------------ UTILITIES ------------------
def standardize_name(name):
    """Convert name from 'last, first' format to 'first last' format."""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def get_or_create_user(email, display_name):
    """Get existing user or create new user in database, return formatted name."""
    try:
        st.write(f"Checking database for user: {email}")
        
        # Check if user exists by email
        result = supabase.table("users").select("user_id, user_name").eq("user_email", email).execute()
        st.write(f"Database query result: {result.data}")
        
        if result.data:
            # User exists, return their name
            st.success(f"Existing user found: {result.data[0]['user_name']}")
            return result.data[0]["user_name"]
        else:
            # New user - create account
            standardized_name = standardize_name(display_name)
            st.write(f"Creating new user: {standardized_name} ({email})")
            
            insert_result = supabase.table("users").insert({
                "user_email": email,
                "user_name": standardized_name,
            }).execute()
            
            st.write(f"Insert result: {insert_result.data}")
            st.success(f"New user created: {standardized_name}")
            logging.info(f"New user created: {email} ({standardized_name})")
            return standardized_name
    except Exception as e:
        st.error(f"Database error in get_or_create_user: {e}")
        logging.error(f"Database error in get_or_create_user: {e}")
        import traceback
        st.code(traceback.format_exc())
        return standardize_name(display_name)

# ------------------ HANDLE MICROSOFT REDIRECT ------------------
query_params = st.query_params

if "code" in query_params and st.session_state["token"] is None:
    try:
        token = oauth.fetch_token(
            url=TOKEN_URL,
            grant_type="authorization_code",
            code=query_params["code"],
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
        )
        st.session_state["token"] = token
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        logging.error(f"OAuth token fetch error: {e}")

# ------------------ LOGGED-IN FLOW ------------------
token = st.session_state["token"]

if token:
    # Get user info from token
    try:
        import jwt
        
        # Debug: Show what we received
        st.write("🔍 **DEBUG: Token received**")
        st.write(f"Token keys: {list(token.keys())}")
        
        # Try to decode access_token or id_token
        token_to_decode = token.get("id_token") or token.get("access_token")
        
        if not token_to_decode:
            st.error("No valid token found in response")
            st.write(f"Token content: {token}")
        else:
            decoded = jwt.decode(token_to_decode, options={"verify_signature": False})
            st.write(f"Decoded token claims: {decoded}")
            
            user_email = decoded.get("preferred_username") or decoded.get("email") or decoded.get("upn") or decoded.get("unique_name") or ""
            user_name_raw = decoded.get("name", "Unknown User")
            
            st.write(f"Extracted email: {user_email}")
            st.write(f"Extracted name: {user_name_raw}")
            
            # Format name
            if "," in user_name_raw:
                last, first = [x.strip() for x in user_name_raw.split(",", 1)]
                user_name = f"{first} {last}"
            else:
                user_name = user_name_raw.strip()
            
            if not st.session_state.logged_in:
                username = get_or_create_user(user_email, user_name)
                st.session_state.logged_in = True
                st.session_state.username = user_email  # Store email for database lookups
                st.session_state.display_name = username  # Store formatted name for display
                st.session_state.user_email = user_email  # Also store email explicitly
                logging.info(f"User logged in: {username} ({user_email})")
            
            st.success(f"Welcome, **{st.session_state.display_name}**!")
            st.page_link("Home.py", label="Click here to go to Home", icon="🏠︎")
            
            if st.button("Log out"):
                st.session_state.clear()
                st.rerun()
    
    except Exception as e:
        st.error(f"Error processing authentication: {e}")
        logging.error(f"Token processing error: {e}")
        import traceback
        st.code(traceback.format_exc())
        if st.button("Try Again"):
            st.session_state.clear()
            st.rerun()

# ------------------ LOGIN BUTTON (NOT LOGGED IN) ------------------
else:
    # Create auth URL with resource parameter for v1.0 endpoint
    auth_url, _ = oauth.create_authorization_url(
        AUTHORIZE_URL,
        prompt="select_account",
        resource=CLIENT_ID,  # v1.0 uses resource parameter instead of scope
    )
    
    st.markdown("### Sign in to DXC Step Tracker")
    st.write("Please sign in with your Microsoft account to access the application.")
    st.link_button("Sign in with Microsoft", auth_url, type="primary")

# ------------------ SIDEBAR ------------------
if st.session_state.logged_in:
    if render_sidebar_welcome(st.session_state.username):
        st.session_state.clear()
        st.rerun()

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()
