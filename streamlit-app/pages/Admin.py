import streamlit as st
import time

def render():
    # Ensure session defaults exist
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    # Protected: require login
    if not st.session_state.get("logged_in"):
        st.warning("You must be logged in to view this page.")
        st.markdown("[Go to Login page](?page=Login)")
        return

    # Logged-in view
    username = st.session_state.get("username", "user")
    st.header(f"Hello {username}")
    st.write("Protected admin content goes here.")

    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        # remove any login inputs left in session state
        for key in ("login_user", "login_pwd", "prot_user", "prot_pwd"):
            st.session_state.pop(key, None)
        st.info("You have been logged out — Please refresh this window.")
        st.stop()

# Run when the page is loaded
render()