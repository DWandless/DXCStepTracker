import streamlit as st
from db import supabase  # import your Supabase client

def render():
    # --- Session defaults ---
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    st.title("Admin Portal")

    # --- Check login ---
    if not st.session_state.get("logged_in"):
        st.warning("You must be logged in to view this page.")
        return

    username = st.session_state.get("username")

    # --- Fetch user record ---
    response = supabase.table("users").select("user_admin").eq("user_name", username).limit(1).execute()

    # Handle errors or missing user
    if not response.data or len(response.data) == 0:
        st.error("User not found.")
        return

    is_admin = response.data[0].get("user_admin", False)

    # --- Check admin status ---
    if not is_admin:
        st.warning("You must be an admin to view this page.")
        return

    # --- Admin-only content ---
    st.header(f"Welcome Admin, {username}")
    st.write("Protected admin content goes here.")

    # Sidebar info
    st.sidebar.markdown(f"**User:** {username}")

    # Optional logout button
    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        for key in ("login_user", "login_pwd", "prot_user", "prot_pwd"):
            st.session_state.pop(key, None)
        st.success("You have been logged out.")
        st.stop()

# Run page
render()