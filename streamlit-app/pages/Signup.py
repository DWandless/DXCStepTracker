import streamlit as st
from db import supabase
import bcrypt
import re
import logging
from pathlib import Path
from components import apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome, hide_streamlit_branding, handle_logout

# ------------------ CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Create an Account", layout="wide", page_icon=logo_path2)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("Create an Account", "Join the DXC Step Challenge and make a difference!")

# ------------------ LOGGING SETUP ------------------
logging.basicConfig(filename="app.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ------------------ INPUT SANITIZATION ------------------
def sanitize_username(username: str) -> str:
    username = username.strip()
    if not re.match(r"^[A-Za-z0-9 _.-]{3,50}$", username):
        raise ValueError(
            "Username must be 3–50 characters long and contain only letters, numbers, spaces, dots, underscores, or hyphens."
        )
    return username

# ------------------ PASSWORD VALIDATION ------------------
def validate_password(password: str) -> bool:
    """Require at least 8 chars, one letter, one digit, one special char."""
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$', password))

# ------------------ REGISTER USER FUNCTION ------------------
def register_user(username: str, password: str, is_admin: bool = False):
    try:
        username = sanitize_username(username)
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        response = supabase.table("users").insert({
            "user_name": username,
            "user_password": hashed_password,
            "user_admin": is_admin
        }).execute()
        return response

    except Exception as e:
        logging.error(f"Signup error for {username}: {e}")
        return None

# ------------------ REGISTRATION FORM ------------------
st.subheader("Sign Up")
st.write("Fill in the details below to create your account.")

with st.form("signup_form"):
    username = st.text_input("Enter your full name")
    password = st.text_input("Choose a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")
    is_admin = False  # Always false for security

    submitted = st.form_submit_button("Register")

    if submitted:
        # --- Input Checks ---
        if not username or not password or not confirm_password:
            st.warning("Please fill out all fields.")
            st.stop()

        try:
            username = sanitize_username(username)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        if password != confirm_password:
            st.error("Passwords do not match.")
        elif not validate_password(password):
            st.error("Password must be at least 8 characters, include a letter, number, and special character.")
        else:
            try:
                # --- Check for duplicate username ---
                existing = supabase.table("users").select("user_name").eq("user_name", username).execute()
                if existing.data:
                    st.error("That username is already taken.")
                    st.stop()

                # --- Attempt Registration ---
                response = register_user(username, password, is_admin)

                if response and response.data:
                    st.success(f"✅ User '{username}' created successfully!")
                    st.page_link("pages/Login.py", label="➡️ Click here to log in.")
                else:
                    st.error("There was an issue creating your account. Please try again.")
            except Exception as e:
                logging.error(f"Unexpected signup error: {e}")
                st.error("An unexpected error occurred. Please contact support.")

# ------------------ SIDEBAR ------------------
if st.session_state.get("username"):
    if render_sidebar_welcome(st.session_state.get('username')):
        handle_logout()

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()