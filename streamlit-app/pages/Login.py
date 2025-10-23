import streamlit as st
import bcrypt
from db import supabase

# ------------------ CONFIG ------------------
st.set_page_config(page_title="🔐 Login", layout="centered")

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
        text-align: center;
        background: linear-gradient(90deg, #603494, #4a2678);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 36px;
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
    /* Footer */
    .footer {
        text-align: center;
        font-size: 14px;
        color: #603494;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HERO HEADER ------------------
header_html = """
<div class="header-container">
    <div class="header-title">Movember Step Tracker 🥸</div>
    <div class="header-subtitle">Log in to start tracking your steps and join the Mo-vement!</div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ------------------ SESSION DEFAULTS ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# ------------------ AUTHENTICATE USER ------------------
def authenticate(username, password):
    try:
        response = supabase.table("users").select("user_password, user_admin").eq("user_name", username).limit(1).execute()
        if response.data and len(response.data) == 1:
            user_data = response.data[0]
            stored_hash = user_data["user_password"].encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
                return "admin" if user_data.get("user_admin", False) else "user"
    except Exception as e:
        st.error(f"Error during authentication: {e}")
    return None

# ------------------ LOGIN FORM ------------------
if st.session_state.logged_in:
    st.info(f"✅ Already logged in as **{st.session_state.username}** ({st.session_state.role}).")
else:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")

    if submitted:
        role = authenticate(username.strip(), password.strip())
        if role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.success(f"✅ Login successful! Role: {role}")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# ------------------ SIDEBAR INFO ------------------
if st.session_state.get("username"):
    st.sidebar.markdown(f"**User:** {st.session_state.username} ({st.session_state.role})")

# ------------------ LOGOUT BUTTON ------------------
if st.session_state.logged_in:
    if st.button("Logout"):
        st.session_state.clear()
        st.success("You have been logged out.")
        st.rerun()

# ------------------ SIGN-UP LINK ------------------
st.markdown("---")
st.page_link("pages/Signup.py", label="📝 Don't have an account? Sign up now")

# ------------------ FOOTER ------------------
st.markdown("<div class='footer'>DXC Technology | Movember 2025</div>", unsafe_allow_html=True)