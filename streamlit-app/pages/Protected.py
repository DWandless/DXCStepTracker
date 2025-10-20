import streamlit as st

def render():
    # Simple access control: Protected page only for logged-in users
    if not st.session_state.get("logged_in"):
        st.warning("You must be logged in to view this page.")
        st.markdown("[Go to Login page](?page=Login)")
        return

    # If logged in, show a single greeting
    username = st.session_state.get("username", "user")
    st.write(f"hello {username}")

# Run when the page is loaded
render()