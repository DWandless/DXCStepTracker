import streamlit as st
import bcrypt
import time
import logging
from db import supabase
from pathlib import Path
from streamlit.components.v1 import html as st_html

# ------------------ CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

st.set_page_config(page_title="🔐 Login", layout="centered", page_icon=logo_path2)

# Resolve logo path so it works from any page
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

# Check if file actually exists
if logo_path.exists():
    st.logo(str(logo_path), icon_image=str(logo_path), size="large")
else:
    st.warning(f"⚠️ Logo not found at: {logo_path}")

# ------------------ STYLES ------------------
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
        text-align: center;
        background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
        color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
    }
    .header-title { font-size: 36px; font-weight: bold; }
    .header-subtitle { font-size: 18px; margin-top: 5px; }
    .stButton>button {
        background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
        color: white; border-radius: 8px;
        font-weight: bold; transition: 0.3s;
        border: none;
    }
    .stButton>button:hover { 
        background: linear-gradient(90deg, #6B94CB, #EF8A5C);
        transform: scale(1.05); 
    }
    .footer-branding { text-align: center; font-size: 14px; color: #666; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="header-container">
    <div class="header-title">DXC Step Tracker</div>
    <div class="header-subtitle">Log in to start tracking your steps!</div>
</div>
""", unsafe_allow_html=True)

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

def logout():
    for key in ("logged_in", "username", "role"):
        st.session_state[key] = ""
    st.session_state.logged_in = False
    st.rerun()

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
    st.sidebar.markdown(f"<h3 style='color:#7BA4DB;'>Welcome, {st.session_state.username}!</h3>", unsafe_allow_html=True)
    if st.sidebar.button("Logout"):
        logout()

# ------------------ SIGN-UP LINK ------------------
st.markdown("---")
st.page_link("pages/Signup.py", label="📝 Don't have an account? Sign up now")

# ------------------ FOOTER ------------------
st.markdown(
    "<div class='footer-branding' style='text-align:center; font-weight:bold; margin-top:40px; padding-top:20px; border-top:2px solid #7BA4DB;'>DXC Technology</div>",
    unsafe_allow_html=True
)

# ------------------ HIDE STREAMLIT STYLE ELEMENTS ------------------
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
