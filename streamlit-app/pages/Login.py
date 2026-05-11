import streamlit as st
import logging
from db import supabase
from pathlib import Path
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

# ------------------ SESSION DEFAULTS ------------------
defaults = {
    "logged_in": False,
    "username": "",
    "role": "",
    "display_name": "",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ------------------ UTILITIES ------------------
def standardize_name(name):
    """Convert name from 'last, first' format to 'first last' format."""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def get_or_create_user(email, display_name):
    """Get existing user or create new user in database, return role."""
    try:
        result = supabase.table("users").select("role").eq("user_email", email).execute()
        if result.data:
            return result.data[0]["role"]
        else:
            standardized_name = standardize_name(display_name)
            supabase.table("users").insert({
                "user_email": email,
                "user_name": standardized_name,
                "user_password": "",
                "role": "user",
            }).execute()
            return "user"
    except Exception as e:
        logging.error(f"Database error: {e}")
        return "user"

# ------------------ LOGIN FLOW ------------------
user_is_logged_in = getattr(st.user, "is_logged_in", False)

if user_is_logged_in:
    email = st.user.email
    display_name = st.user.name or email
    
    if not st.session_state.logged_in:
        role = get_or_create_user(email, display_name)
        st.session_state.logged_in = True
        st.session_state.username = email
        st.session_state.role = role
        st.session_state.display_name = standardize_name(display_name)
    
    st.success(f"Welcome, **{st.session_state.display_name}**!")
    st.info(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    st.page_link("Home.py", label=" 🏠︎ Click here to go to the home page.")
    st.button("Log out", on_click=st.logout)
else:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.display_name = ""
    st.button("Sign in with Microsoft", on_click=st.login)

# ------------------ SIDEBAR ------------------
if st.session_state.logged_in:
    if render_sidebar_welcome(st.session_state.username):
        st.logout()
        st.rerun()

# ------------------ SIGN-UP LINK ------------------
st.markdown("---")
st.page_link("pages/Signup.py", label="🗎 Don't have an account? Sign up now")

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()
