import streamlit as st
import bcrypt
from db import supabase

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Login", layout="centered")
st.title("🔐 Log In")

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
    st.info(f"Already logged in as **{st.session_state.username}** ({st.session_state.role}).")
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
            st.rerun()  # ✅ Updated
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
        st.rerun()  # ✅ Updated

# ------------------ SIGN-UP LINK ------------------
st.markdown("---")
st.page_link("pages/Signup.py", label="📝 Don't have an account? Sign up now")