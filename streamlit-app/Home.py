import streamlit as st
from datetime import datetime
from db import supabase
import os

def get_user_id(username):
    """Fetch user_id from the users table given a username."""
    try:
        response = supabase.table("users").select("user_id").eq("user_name", username).execute()
        if response.data and len(response.data) == 1:
            return response.data[0]["user_id"]
    except Exception as e:
        st.error(f"Error fetching user ID: {e}")
    return None

def render():
    st.set_page_config(page_title="Movember Step Tracker", layout="wide")
    st.title("Movember Step Tracker")

    # --- Check session ---
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.warning("You must be logged in to view this page.")
        return

    username = st.session_state.get("username", "")

    user_id = get_user_id(username)
    if user_id is None:
        st.error("User ID could not be found.")
        return

    # --- Form ---
    st.header(f"Welcome, {username}! 👟")
    st.write("Submit your daily steps below:")

    with st.form("step_form"):
        step_date = st.date_input("Date")
        steps = st.number_input("Step Count", min_value=0, step=100)
        screenshot = st.file_uploader("Upload Screenshot (PNG/JPEG)", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Submit")

        if submitted:
            if not screenshot:
                st.error("Please upload a screenshot.")
            else:
                filename = f"{username}_{step_date}_{datetime.now().strftime('%H%M%S')}_{screenshot.name}"
                uploads_dir = "uploads"
                os.makedirs(uploads_dir, exist_ok=True)
                filepath = os.path.join(uploads_dir, filename)

                with open(filepath, "wb") as f:
                    f.write(screenshot.read())

                # Insert into Supabase — now using try/except
                try:
                    supabase.table("forms").insert({
                        "form_filepath": filename,
                        "form_stepcount": steps,
                        "form_date": str(step_date),
                        "user_id": user_id
                    }).execute()
                    st.success("Step count submitted successfully!")
                except Exception as e:
                    st.error(f"Error submitting form: {e}")
    
    # --- Logout Button ---
    if st.sidebar.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        # remove any login inputs left in session state
        for key in ("login_user", "login_pwd", "prot_user", "prot_pwd"):
            st.session_state.pop(key, None)
        st.info("You have been logged out — Please refresh this window.")
        st.stop()
    
    # show logged-in user (if any)
    if st.session_state.get("username"):
        st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")
        
# Run it
render()