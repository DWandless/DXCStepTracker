import streamlit as st
from db import supabase
import bcrypt
import re
import logging
from pathlib import Path
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome,
                        hide_streamlit_branding, handle_logout, setup_logging, sanitize_username,
                        validate_password, register_user)

# ------------------ CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Create an Account", layout="wide", page_icon=logo_path2)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("Create an Account", "Join the DXC Step Challenge and make a difference!")

# ------------------ LOGGING SETUP ------------------
setup_logging()

# ------------------ VALIDATION & REGISTRATION ------------------
# Validation and registration functions now imported from components

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