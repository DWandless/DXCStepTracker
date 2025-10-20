import streamlit as st
import time

# Demo credentials (keep in sync with pages/protected.py or move to a shared module)
CREDENTIALS = {"alice": "password123", "bob": "hunter2"}

def authenticate(user: str, pwd: str) -> bool:
    return CREDENTIALS.get(user) == pwd

def _navigate_to_page(page_name: str):
    """Try several ways to navigate to another Streamlit page (multipage)."""
    # Preferred: set query params then rerun
    try:
        setter = getattr(st, "experimental_set_query_params", None)
        if callable(setter):
            setter(page=page_name)
    except Exception:
        pass

    # older API
    try:
        setter = getattr(st, "set_query_params", None)
        if callable(setter):
            setter(page=page_name)
    except Exception:
        pass

    # Try to force a rerun
    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            rerun()
            return
    except Exception:
        pass

    # Fallback: provide direct link the user can click
    st.success("Login successful — click the link below if the app did not navigate automatically.")
    st.markdown(f"[Go to {page_name}](?page={page_name})")
    st.stop()

def render():
    st.title("Log in")

    # session defaults
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if st.session_state.logged_in:
        st.info(f"Already logged in as **{st.session_state.username}**. Go to the Protected page from the Pages menu.")
        return

    st.write("Enter your username and password to sign in.")

    with st.form("login_form"):
        user = st.text_input("Username", key="login_user")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if authenticate(user, pwd):
            st.session_state.logged_in = True
            st.session_state.username = user
            # clear sensitive fields
            st.session_state.pop("login_pwd", None)
            st.success("Logged in")
            # try to navigate to the Protected page
            _navigate_to_page("Protected")
        else:
            st.error("Invalid credentials")

# run UI when page is loaded
render()