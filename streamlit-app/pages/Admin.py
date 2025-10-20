import streamlit as st
import time

def _navigate_to_page(page_name: str):
    """Navigate to another Streamlit multipage page if possible, else show link."""
    try:
        setter = getattr(st, "query_params", None)
        if callable(setter):
            setter(page=page_name, _ts=int(time.time()))
    except Exception:
        pass

    try:
        setter2 = getattr(st, "set_query_params", None)
        if callable(setter2):
            setter2(page=page_name, _ts=int(time.time()))
    except Exception:
        pass

    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            rerun()
            return
    except Exception:
        pass

    st.info("You have been logged out — click the link below if the app did not navigate automatically.")
    st.markdown(f"[Go to {page_name}](?page={page_name})")
    st.stop()

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
        _navigate_to_page("Login")

# Run when the page is loaded
render()