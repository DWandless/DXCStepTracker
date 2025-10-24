import streamlit as st
from db import supabase
import bcrypt
import time
import random
import re

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Create an Account", layout="wide")

# ------------------ DXC BRANDING & MOVEMBER CSS ------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #FFFFFF;
    }
    /* Hero Header */
    .header-container {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        background: linear-gradient(90deg, #603494, #4a2678);
        color: white;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 42px;
        font-weight: bold;
    }
    .header-subtitle {
        font-size: 18px;
        margin-top: 5px;
    }
    /* Buttons */
    .stButton>button {
        background-color: #603494;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #4a2678;
        transform: scale(1.05);
    }
    /* Footer Carousel */
    .footer-carousel {
        text-align: center;
        font-size: 18px;
        color: #603494;
        font-weight: bold;
        margin-top: 30px;
        padding: 10px;
        border-top: 2px solid #603494;
    }
    .footer-branding {
        text-align: center;
        font-size: 14px;
        color: #666;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HERO HEADER ------------------
header_html = """
<div class="header-container">
    <div>
        <div class="header-title">Create an Account 🥸</div>
        <div class="header-subtitle">Join the Movember Step Challenge and make a difference!</div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ------------------ INPUT SANITIZATION FUNCTION ------------------
def sanitize_username(username: str) -> str:
    username = username.strip()
    if not re.match(r"^[A-Za-z0-9 _.-]{3,50}$", username):
        raise ValueError("Username must be 3–50 characters long and contain only letters, numbers, spaces, dots, underscores, or hyphens.")
    return username


# ------------------ REGISTER USER FUNCTION ------------------
def register_user(username: str, password: str, is_admin: bool = False):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        username = sanitize_username(username)
    except ValueError as e:
        st.error(str(e))

    response = supabase.table("users").insert({
        "user_name": username,
        "user_password": hashed_password,
        "user_admin": is_admin
    }).execute()
    return response

# ------------------ REGISTRATION FORM ------------------
st.subheader("Sign Up")
st.write("Fill in the details below to create your account.")

with st.form("signup_form"):
    username = st.text_input("Enter your full name")
    password = st.text_input("Choose a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")
    is_admin = False  # Default is non-admin
    submitted = st.form_submit_button("Register")

    if submitted:
        if not username or not password or not confirm_password:
            st.warning("Please fill out all fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif len(password) < 8 or not any(c.isdigit() for c in password) or not any(c.isalpha() for c in password):
            st.error("Password must be at least 8 characters long and include both letters and numbers.")
        else:
            existing = supabase.table("users").select("user_name").eq("user_name", username).execute()
            if existing.data:
                st.error("That username is already taken.")
            else:
                register_user(username, password, is_admin)
                st.success(f"✅ User '{username}' created successfully! You can now log in.")

# ------------------ SIDEBAR ------------------
if st.session_state.get("username"):
    st.sidebar.markdown(f"<h3 style='color:#603494;'>Welcome, {st.session_state.get('username')}!</h3>", unsafe_allow_html=True)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ------------------ FOOTER CAROUSEL ------------------
carousel_messages = [
    "💡 Movember Tip: Walking meetings are a great way to add steps!",
    "🥸 Fun Fact: A mustache can grow up to 0.4mm per day!",
    "🚶 Challenge: Hit 10,000 steps today and celebrate with a Mo-selfie!",
    "💜 DXC supports Movember: Keep moving, keep growing!",
    "🔥 Did you know? Just 30 minutes of walking can boost your mood and health!",
    "🎯 Goal Reminder: Every step counts toward a healthier you and a great cause!",
    "📸 Share your Mo! Post your mustache progress and inspire others!",
    "🏆 Leaderboard Alert: Check who's leading the Mo-vement today!",
    "🌍 Together we can make a difference—one step at a time!",
    "💪 Pro Tip: Take the stairs instead of the elevator for an easy step boost!",
    "🎉 Fun Challenge: Invite a colleague for a lunchtime walk and double your steps!",
    "🥳 Celebrate small wins! Every 1,000 steps is a victory for your health!"
]

# Show one random message per page load
carousel_placeholder = st.empty()
msg = random.choice(carousel_messages)
carousel_placeholder.markdown(
    f"<div class='footer-carousel'>{msg}</div>",
    unsafe_allow_html=True
)

# Render branding once (static)
st.markdown(
    "<div class='footer-branding' style='color:#603494; text-align:center; font-weight:bold; margin-top:20px;'>DXC Technology | Movember 2025</div>",
    unsafe_allow_html=True
)