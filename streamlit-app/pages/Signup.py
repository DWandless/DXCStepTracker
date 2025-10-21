import streamlit as st
from db import supabase
import bcrypt

def register_user(username: str, password: str, is_admin: bool = False):
    # Hash the password before storing
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Insert user into Supabase
    response = supabase.table("users").insert({
        "user_name": username,
        "user_password": hashed_password,
        "user_admin": is_admin
    }).execute()

    return response

def render():
    st.title("Create an Account")
    st.write("Register a new user below.")

    with st.form("signup_form"):
        username = st.text_input("Choose a username")
        password = st.text_input("Choose a password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")
        is_admin = False # Default is non-admin; modify as needed
        submitted = st.form_submit_button("Register")

        if submitted:
            if not username or not password or not confirm_password:
                st.warning("Please fill out all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Optional: check if username already exists
                existing = supabase.table("users").select("user_name").eq("user_name", username).execute()
                if existing.data:
                    st.error("That username is already taken.")
                else:
                    register_user(username, password, is_admin)
                    st.success(f"User '{username}' created successfully!")

# show logged-in user (if any)
if st.session_state.get("username"):
    st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")

render()