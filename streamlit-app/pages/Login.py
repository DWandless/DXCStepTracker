import streamlit as st
from db import supabase

def authenticate(user: str, pwd: str) -> bool:
    response = supabase.table("users").select("*").eq("user_name", user).execute()
    
    if response.data and len(response.data) == 1:
        user_record = response.data[0]
        stored_password = user_record.get("user_password", "")
        return pwd == stored_password
    
    return False

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

    # show logged-in user
    if st.session_state.get("username"):
        st.sidebar.markdown(f"**User:** {st.session_state.get('username')}")

# run UI when page is loaded
render()