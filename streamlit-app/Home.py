import streamlit as st
import os
import pandas as pd
from datetime import datetime
import plotly.express as px
import zipfile
import io
from db import supabase

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Movember Step Tracker", layout="wide")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ HELPER FUNCTIONS ------------------
def get_user_id(username):
    try:
        response = supabase.table("users").select("user_id").eq("user_name", username).execute()
        if response.data and len(response.data) == 1:
            return response.data[0]["user_id"]
    except Exception as e:
        st.error(f"Error fetching user ID: {e}")
    return None

def fetch_user_forms(user_id):
    try:
        response = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching forms: {e}")
        return pd.DataFrame()

# ------------------ LOGIN CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username", "Guest")
user_id = get_user_id(username)
if not user_id:
    st.error("User ID not found.")
    st.stop()

# ------------------ HEADER ------------------
st.title("🏃 Movember Step Tracker")
st.sidebar.success(f"Welcome, {username}!")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.info("You have been logged out. Refresh the page.")
    st.stop()

# ------------------ TABS ------------------
tab1, tab2, tab3 = st.tabs(["➕ Submit Steps", "📊 Daily Progress", "📂 All Submissions"])

# ------------------ TAB 1: SUBMIT STEPS ------------------
with tab1:
    st.header("Submit Your Steps")
    col1, col2 = st.columns(2)
    with col1:
        step_date = st.date_input("Date")
    with col2:
        steps = st.number_input("Step Count", min_value=0, step=100)

    screenshot = st.file_uploader("Upload Screenshot (PNG/JPEG)", type=["png", "jpg", "jpeg"])
    if screenshot:
        st.image(screenshot, caption="Preview", width=300)

    if st.button("Submit"):
        if not screenshot:
            st.error("Please upload a screenshot.")
        else:
            filename = f"{username}_{step_date}_{datetime.now().strftime('%H%M%S')}_{screenshot.name}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(screenshot.getbuffer())

            try:
                supabase.table("forms").insert({
                    "form_filepath": filename,
                    "form_stepcount": steps,
                    "form_date": str(step_date),
                    "user_id": user_id,
                    "form_verified": False
                }).execute()
                st.success("✅ Step count submitted successfully!")
                st.balloons()
            except Exception as e:
                st.error(f"Error submitting form: {e}")

# ------------------ TAB 2: DAILY PROGRESS ------------------
with tab2:
    st.header("Daily Progress")
    df = fetch_user_forms(user_id)
    if not df.empty:
        daily_steps = df.groupby("form_date")["form_stepcount"].sum().reset_index()
        st.metric("Your Total Steps", int(df["form_stepcount"].sum()))
        fig = px.bar(daily_steps, x="form_date", y="form_stepcount", title=f"{username}'s Steps per Day")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No submissions yet.")

# ------------------ TAB 3: ALL SUBMISSIONS ------------------
with tab3:
    st.header("Your Submissions")
    df = fetch_user_forms(user_id)
    if not df.empty:
        st.dataframe(df[["form_date", "form_stepcount", "form_filepath"]], use_container_width=True)

        # Download CSV
        csv_data = df.to_csv(index=False)
        st.download_button("Download My Data (CSV)", csv_data, f"{username}_steps.csv")

        # Download Screenshots as ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_name in df["form_filepath"]:
                file_path = os.path.join(UPLOAD_FOLDER, file_name)
                if os.path.exists(file_path):
                    zip_file.write(file_path, arcname=os.path.basename(file_path))
        zip_buffer.seek(0)
        st.download_button("Download My Screenshots (ZIP)", zip_buffer, f"{username}_screenshots.zip")
    else:
        st.info("You have no submissions yet.")
