import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import zipfile
import io
from PIL import Image, UnidentifiedImageError
import re
import unicodedata
from db import supabase
import random
import html
from pathlib import Path

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Movember Step Tracker", layout="wide")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# add max upload size
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

# Add a top logo in sidebar before Streamlit’s nav
st.logo("assets/logo.png", icon_image="assets/logo.png", size="large")  # Works for sidebar and top-left favicon


# ------------------ DXC BRANDING & MOVEMBER CSS ------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #FFFFFF;
    }
    /* Hero Header */
    .header-container {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        background: linear-gradient(90deg, #603494, #4a2678);
        color: white;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 42px;
        font-weight: bold;
    }
    .header-subtitle {
        font-size: 18px;
        margin-top: 5px;
    }
    /* Tabs */
    .stTabs [role="tablist"] {
        border-bottom: 3px solid #603494;
    }
    .stTabs [role="tab"] {
        color: #603494;
        font-weight: bold;
    }
    /* Buttons */
    .stButton>button {
        background-color: #603494;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #4a2678;
        transform: scale(1.05);
    }
    /* Footer Carousel */
    .footer-carousel {
        text-align: center;
        font-size: 18px;
        color: #603494;
        font-weight: bold;
        margin-top: 30px;
        padding: 10px;
        border-top: 2px solid #603494;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HERO HEADER ------------------
st.markdown("""
<div class="header-container">
    <div>
        <div class="header-title">🏃 Movember Step Tracker</div>
        <div class="header-subtitle">Track your steps, make every move count for men's health!</div>
    </div>
</div>
""", unsafe_allow_html=True)
# ------------------ SECURE FILENAME HELPER ------------------
def secure_filename(filename: str, max_length: int = 255) -> str:
    if not filename:
        return "file"
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9.\-_]", "_", filename)
    return filename[:max_length]

# ------------------ HELPER FUNCTIONS ------------------
def get_user_id(username):
    try:
        response = supabase.table("users").select("user_id").eq("user_name", username).execute()
        if response.data and len(response.data) == 1:
            return response.data[0]["user_id"]
    except Exception:
        pass
    return None

def fetch_user_forms(user_id):
    try:
        response = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def get_last_submission_time(user_id):
    try:
        response = (
            supabase.table("forms")
            .select("form_created_at")
            .eq("user_id", user_id)
            .order("form_created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) == 1:
            return datetime.fromisoformat(response.data[0]["form_created_at"])
    except Exception:
        pass
    return None

# ------------------ LOGIN CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username")
user_id = get_user_id(username)
if not user_id:
    st.error("User account not found.")
    st.stop()

safe_username = html.escape(username)

# ------------------ SIDEBAR ------------------
st.sidebar.markdown(f"<h3 style='color:#603494;'>Welcome, {safe_username}!</h3>", unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4 = st.tabs(["➕ Submit Steps", "📊 Daily Progress", "📂 All Submissions", "💜 About Movember"])

# ------------------ TAB 1: SUBMIT STEPS ------------------
with tab1:
    st.header("Submit Your Steps")
    col1, col2 = st.columns(2)
    with col1:
        step_date = st.date_input("Date")
    with col2:
        steps = st.number_input("Step Count", min_value=0, step=100)

    screenshot = st.file_uploader(
        "Upload Screenshot (PNG/JPEG)",
        type=["png", "jpg", "jpeg"]
    )

    if screenshot:
        if screenshot.size > MAX_UPLOAD_SIZE:
            st.error("File too large. Max 5 MB.")
            st.stop()
        try:
            img = Image.open(screenshot)
            img.thumbnail((600, 600))
            st.image(img, caption="Preview", width=300)
        except UnidentifiedImageError:
            st.error("Uploaded file is not a valid image.")
            st.stop()

    if "last_submission_time" not in st.session_state:
        st.session_state.last_submission_time = None

    if st.button("Submit"):
        now = datetime.now()
        last_submission = st.session_state.last_submission_time or get_last_submission_time(user_id)

        if last_submission and now - last_submission < timedelta(minutes=5):
            remaining = timedelta(minutes=5) - (now - last_submission)
            minutes, seconds = divmod(remaining.total_seconds(), 60)
            st.warning(f"⏳ Wait {int(minutes)}m {int(seconds)}s before submitting again.")
        else:
            if not screenshot:
                st.error("Please upload a screenshot.")
                st.stop()
            if steps <= 0 or steps > 100000:
                st.error("Enter a valid step count between 1 and 100,000.")
                st.stop()

            try:
                img = Image.open(screenshot).convert("RGB")
                raw_name = f"{safe_username}_{step_date}_{datetime.now().strftime('%H%M%S')}_{screenshot.name}"
                filename = secure_filename(raw_name)
                filename = os.path.splitext(filename)[0] + ".jpg"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                img.save(file_path, format="JPEG", quality=85, optimize=True)
                try:
                    os.chmod(file_path, 0o600)
                except Exception:
                    pass

                supabase.table("forms").insert({
                    "form_filepath": filename,
                    "form_stepcount": steps,
                    "form_date": str(step_date),
                    "user_id": user_id,
                    "form_verified": False
                }).execute()

                # Delete the image if steps are under 10,000, not required for verification
                if steps < 10000:
                    try:
                        os.remove(file_path)
                    except FileNotFoundError:
                        pass

                st.session_state.last_submission_time = now
                st.success("✅ Step count submitted successfully!")
                st.balloons()
            except UnidentifiedImageError:
                st.error("Uploaded file is not a valid image.")
            except Exception:
                st.error("Error processing uploaded image.")

# ------------------ TAB 2: DAILY PROGRESS ------------------
with tab2:
    st.header("Daily Progress")
    df = fetch_user_forms(user_id)
    if not df.empty:
        daily_steps = df.groupby("form_date")["form_stepcount"].sum().reset_index()
        total_steps = int(df["form_stepcount"].sum())

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Steps", total_steps)
        today_steps = int(daily_steps[daily_steps["form_date"] == str(datetime.now().date())]["form_stepcount"].sum() or 0)
        col2.metric("Steps Today", today_steps)
        col3.metric("Days Participated", daily_steps["form_date"].nunique())

        col4, col5, col6 = st.columns(3)
        col4.metric("Average Daily Steps", int(daily_steps["form_stepcount"].mean()))
        col5.metric("Estimated Distance (km)", round(total_steps * 0.0008, 2))
        col6.metric("Estimated Calories Burned", int(total_steps * 0.04))

        daily_steps["form_date"] = pd.to_datetime(daily_steps["form_date"]).dt.date
        sorted_dates = sorted(daily_steps["form_date"].unique())

        # Calculate streak
        streak = 0
        current_streak = 1 if sorted_dates else 0
        for i in range(len(sorted_dates) - 1, 0, -1):
            if (sorted_dates[i] - sorted_dates[i - 1]) == timedelta(days=1):
                current_streak += 1
            else:
                break
        if sorted_dates and sorted_dates[-1] != datetime.now().date():
            current_streak = 0
        streak = current_streak

        if streak > 0:
            st.success(f"🔥 Current Streak: {streak} day{'s' if streak > 1 else ''}!")
        else:
            st.info("No active streak.")

        fig = px.bar(
            daily_steps, x="form_date", y="form_stepcount",
            title=f"{safe_username}'s Steps per Day",
            color_discrete_sequence=["#603494"],
            labels={"form_date": "Date", "form_stepcount": "Step Count"},
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No submissions yet.")

# ------------------ TAB 3: ALL SUBMISSIONS ------------------
with tab3:
    st.header("Your Submissions")
    df = fetch_user_forms(user_id)
    if not df.empty:
        st.dataframe(df[["form_date", "form_stepcount", "form_filepath"]], width="stretch")

        csv_data = df.to_csv(index=False)
        st.download_button("Download CSV", csv_data, f"{secure_filename(safe_username)}_steps.csv")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_name in df["form_filepath"]:
                safe_name = secure_filename(os.path.basename(str(file_name)))
                file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                if os.path.exists(file_path):
                    zip_file.write(file_path, arcname=os.path.basename(safe_name))
        zip_buffer.seek(0)
        st.download_button("Download Screenshots (ZIP)", zip_buffer, f"{secure_filename(safe_username)}_screenshots.zip")
    else:
        st.info("No submissions yet.")

# ------------------ TAB 4: ABOUT MOVEMBER ------------------
with tab4:
    st.header("About Movember")
    st.markdown(""" 
    **Movember** is a global movement committed to changing the face of men's health.
    Every November, participants grow mustaches and take on fitness challenges to raise
    awareness and funds for:

    - 🧠 **Mental Health & Suicide Prevention**  
    - 💪 **Prostate Cancer Research**  
    - 🩺 **Testicular Cancer Support**

    ### 🚶 Why Steps?
    Physical activity plays a major role in both physical and mental well-being.  
    By tracking your steps, you’re not only improving your health — you’re also supporting
    Movember’s mission for men everywhere.

    ---
    ### 📚 Learn More
    - [Movember Official Website](https://uk.movember.com)
    - [Men’s Health Resources](https://movember.com/mens-health)
    - [Get Involved / Donate](https://uk.movember.com/get-involved)
    - [DXC Official Website](https://dxc.com)
    """)

# ------------------ FOOTER CAROUSEL ------------------
carousel_messages = [
    "💡 Movember Tip: Walking meetings are a great way to add steps!",
    "🥸 Fun Fact: A mustache can grow up to 0.4mm per day!",
    "🚶 Challenge: Hit 10,000 steps today and celebrate with a Mo-selfie!",
    "💜 DXC supports Movember: Keep moving, keep growing!",
    "🔥 Did you know? Just 30 minutes of walking can boost your mood and health!",
    "🎯 Goal Reminder: Every step counts toward a healthier you and a great cause!",
    "📸 Share your Mo! Post your mustache progress and inspire others!",
    "🏆 Leaderboard Alert: Check who's leading the Mo-vement today!",
    "🌍 Together we can make a difference—one step at a time!",
    "💪 Pro Tip: Take the stairs instead of the elevator for an easy step boost!",
    "🎉 Fun Challenge: Invite a colleague for a lunchtime walk and double your steps!",
    "🥳 Celebrate small wins! Every 1,000 steps is a victory for your health!"
]
msg = random.choice(carousel_messages)
st.markdown(f"<div class='footer-carousel'>{msg}</div>", unsafe_allow_html=True)
st.markdown("<div class='footer-branding' style='color:#603494; text-align:center; font-weight:bold; margin-top:20px;'>DXC Technology | Movember 2025</div>", unsafe_allow_html=True)
