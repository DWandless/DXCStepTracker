import streamlit as st
import bcrypt
import time
import logging
from db import supabase
from pathlib import Path
from components import apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome, hide_streamlit_branding, handle_logout

# ------------------ CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="🔐 Login", layout="centered", page_icon=logo_path2)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("DXC Step Tracker", "Log in to start tracking your steps!")

# ------------------ LOGGING ------------------
logging.basicConfig(filename="app.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------ SESSION DEFAULTS ------------------
defaults = {
    "logged_in": False,
    "username": "",
    "role": "",
    "login_attempts": 0,
    "lockout_time": 0,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ------------------ UTILITIES ------------------
def sanitize_username(username: str) -> str:
    username = username.strip()
    if not username or len(username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    return username

# Logout function now imported from components

# ------------------ AUTHENTICATION ------------------
def authenticate(username, password):
    """Verify credentials securely and return role or None."""
    FAKE_HASH = bcrypt.hashpw(b"fakepassword", bcrypt.gensalt())  # for timing defense
    try:
        response = supabase.table("users").select("user_password, user_admin").eq("user_name", username).limit(1).execute()

        if response.data and len(response.data) == 1:
            user_data = response.data[0]
            stored_hash = user_data["user_password"].encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
                return "admin" if user_data.get("user_admin", False) else "user"
        else:
            bcrypt.checkpw(password.encode("utf-8"), FAKE_HASH)
            return None

    except Exception as e:
        logging.error("Authentication error for this user, please try again later.")
        time.sleep(1)
        return None

# ------------------ LOGIN FLOW ------------------
if st.session_state.lockout_time > time.time():
    st.error("Too many failed attempts. Please wait a few seconds and try again.")
    st.stop()

if st.session_state.logged_in:
    st.info(f"✅ Logged in as **{st.session_state.username}** ({st.session_state.role})")
    st.page_link("Home.py", label="➡️ Click here to go to the home page.")
else:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        try:
            username = sanitize_username(username)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        role = authenticate(username, password)

        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.session_state.login_attempts = 0
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.session_state.login_attempts += 1
            st.error("Invalid username or password.")

            if st.session_state.login_attempts >= 5:
                st.session_state.lockout_time = time.time() + 30  # 30-second cooldown
                st.warning("Too many failed attempts. Please wait 30 seconds.")

# ------------------ SIDEBAR ------------------
if st.session_state.logged_in:
    if render_sidebar_welcome(st.session_state.username):
        handle_logout()

# ------------------ SIGN-UP LINK ------------------
st.markdown("---")
st.page_link("pages/Signup.py", label="📝 Don't have an account? Sign up now")

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()
