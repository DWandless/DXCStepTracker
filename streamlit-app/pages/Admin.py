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
        return

    # Logged-in view
    username = st.session_state.get("username", "user")
    st.header(f"Hello {username}")
    st.write("Protected admin content goes here.")

    # show logged-in user
    if st.session_state.get("username"):
        st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")

# Run when the page is loaded
render()