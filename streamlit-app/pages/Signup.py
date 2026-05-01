import streamlit as st
from db import supabase
import bcrypt
import re
import random
import logging
from pathlib import Path
from streamlit.components.v1 import html as st_html

# ------------------ CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

st.set_page_config(page_title="Create an Account", layout="wide", page_icon=logo_path2)

# Resolve logo path so it works from any page
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

# Check if file actually exists
if logo_path.exists():
    st.logo(str(logo_path), icon_image=str(logo_path), size="large")
else:
    st.warning(f"⚠️ Logo not found at: {logo_path}")

# ------------------ DXC BRANDING CSS ------------------
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
    .stButton>button {
        background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
        color: white;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #6B94CB, #EF8A5C);
        transform: scale(1.05);
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

# ------------------ HERO HEADER ------------------
st.markdown("""
<div class="header-container">
    <div>
        <div class="header-title">Create an Account</div>
        <div class="header-subtitle">Join the DXC Step Challenge and make a difference!</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
    st.sidebar.markdown(
        f"<h3 style='color:#7BA4DB;'>Welcome, {st.session_state.get('username')}!</h3>",
        unsafe_allow_html=True
    )
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ------------------ FOOTER ------------------
st.markdown(
    "<div class='footer-branding' style='text-align:center; font-weight:bold; margin-top:40px; padding-top:20px; border-top:2px solid #7BA4DB;'>DXC Technology</div>",
    unsafe_allow_html=True
)

# ------------------ HIDE STREAMLIT STYLE ELEMENTS TEST ------------------
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