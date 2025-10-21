import streamlit as st

# Demo credentials (keep in sync with pages/Admin.py or move to a shared module)
CREDENTIALS = {"alice": "password123", "bob": "hunter2"}

def authenticate(user: str, pwd: str) -> bool:
    return CREDENTIALS.get(user) == pwd

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
        else:
            st.error("Invalid credentials")

# run UI when page is loaded
render()