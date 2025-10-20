import streamlit as st

# Demo credentials (keep in sync with pages/Admin.py or move to a shared module)
CREDENTIALS = {"alice": "password123", "bob": "hunter2"}

def authenticate(user: str, pwd: str) -> bool:
    return CREDENTIALS.get(user) == pwd

def _navigate_to_page(page_name: str):
    """Navigate to another Streamlit multipage page if possible, else show link."""
    # Try setting query params (works in many Streamlit versions)
    try:
        setter = getattr(st, "query_params", None)
        if callable(setter):
            setter(page=page_name)
        else:
            setter2 = getattr(st, "set_query_params", None)
            if callable(setter2):
                setter2(page=page_name)
    except Exception:
        pass

    # Try forcing a rerun
    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            rerun()
            return
    except Exception:
        pass


def render():
    st.title("Log in")

    # session defaults
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if st.session_state.logged_in:
        st.info(f"Already logged in as **{st.session_state.username}**. Use the Pages menu to go to Admin.")
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
            st.session_state.pop("login_pwd", None)
            st.success("Login successful — Please navigate to the Admin Page.")
            _navigate_to_page("Admin")
        else:
            st.error("Invalid credentials")

# run UI when page is loaded
render()