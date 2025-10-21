# filepath: streamlit-app/pages/About.py
import streamlit as st

def render():
    st.title("About")
    st.write("Minimal app demonstrating navigation and a protected page.")

# show logged-in user
if st.session_state.get("username"):
    st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")

render()