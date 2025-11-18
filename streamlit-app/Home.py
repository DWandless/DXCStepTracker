import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from PIL import Image, UnidentifiedImageError
import re, unicodedata, random, html, io
from pathlib import Path
from db import supabase
from streamlit.components.v1 import html as st_html

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parent / "assets" / "logo3.png"
st.set_page_config(page_title="🏃 Movember Step Tracker", layout="wide", page_icon=logo_path2)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

# ------------------ LOGO ------------------
logo_path = Path(__file__).parent / "assets" / "logo.png"
st.logo(str(logo_path), icon_image=str(logo_path), size="large")

# ------------------ CUSTOM STYLES ------------------
st.markdown("""
<style>
    body { font-family: 'Roboto', sans-serif; background-color: #fff; }
    .header-container {
        display: flex; justify-content: flex-start; align-items: center;
        background: linear-gradient(90deg, #603494, #4a2678);
        color: white; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-title { font-size: 42px; font-weight: bold; }
    .stButton>button {
        background-color: #603494; color: white; border-radius: 8px;
        font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #4a2678; transform: scale(1.05); }
    .footer-carousel {
        text-align: center; font-size: 18px; color: #603494; font-weight: bold;
        margin-top: 30px; padding: 10px; border-top: 2px solid #603494;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("""
<div class="header-container">
    <div>
        <div class="header-title">🏃 Movember Step Tracker</div>
        <div class="header-subtitle">Track your steps, make every move count for men's health!</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def secure_filename(filename):
    if not filename: return "file"
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKD", filename).encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9.\-_]", "_", filename)
    return filename[:255]

def get_user_id(username):
    try:
        res = supabase.table("users").select("user_id").eq("user_name", username).execute()
        if res.data: return res.data[0]["user_id"]
    except Exception: pass
    return None

def fetch_user_forms(user_id):
    try:
        res = supabase.table("forms").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
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

# ------------------ LOGIN ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username")
user_id = get_user_id(username)
if not user_id:
    st.error("User not found.")
    st.stop()

safe_username = html.escape(username)
st.sidebar.markdown(f"<h3 style='color:#603494;'>Welcome, {safe_username}!</h3>", unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["➕ Submit Steps", "📊 Daily Progress"])

# ------------------ TAB 1: SUBMIT STEPS ------------------
with tab1:
    st.header("➕ Submit Your Steps")
    date_col, step_col = st.columns(2)
    with date_col: step_date = st.date_input("Date")
    with step_col: steps = st.number_input("Step Count", min_value=0, step=100)
    screenshot = st.file_uploader("Upload Screenshot (PNG/JPG)", type=["png", "jpg", "jpeg"])

    if screenshot:
        if screenshot.size > MAX_UPLOAD_SIZE:
            st.error("File too large. Max 5 MB."); st.stop()
        try:
            img = Image.open(screenshot)
            img.thumbnail((600, 600))
            st.image(img, caption="Preview", width=300)
        except UnidentifiedImageError:
            st.error("Invalid image."); st.stop()

    if st.button("Submit"):
        now = datetime.now()
        last_submission = st.session_state.get("last_submission_time") or get_last_submission_time(user_id)

        # --- 1-minute cooldown check ---
        if last_submission and now - last_submission < timedelta(minutes=1): # Brian wicks wanted this changed :)
            remaining = timedelta(minutes=1) - (now - last_submission)
            minutes, seconds = divmod(remaining.total_seconds(), 60)
            st.warning(f"⏳ Please wait {int(minutes)}m {int(seconds)}s before submitting again.")
        elif steps <= 0 or steps > 100000:
            st.error("Enter a valid step count (1–100,000).")
        elif not screenshot:
            st.error("Please upload a screenshot.")
        else:
            try:
                img = Image.open(screenshot).convert("RGB")
                filename = secure_filename(f"{safe_username}_{step_date}_{datetime.now().strftime('%H%M%S')}.jpg")
                path = os.path.join(UPLOAD_FOLDER, filename)
                img.save(path, format="JPEG", quality=85, optimize=True)
                supabase.table("forms").insert({
                    "form_filepath": filename,
                    "form_stepcount": steps,
                    "form_date": str(step_date),
                    "user_id": user_id,
                    "form_verified": False
                }).execute()

                # Delete the image if steps are under 10,000 (not required for verification)
                if steps < 10000:
                    try:
                        os.remove(path)
                    except FileNotFoundError:
                        pass

                # Record new submission time
                st.session_state.last_submission_time = now

                st.success("✅ Step count submitted successfully!")
                st.balloons()
            except Exception as e:
                st.error("Error processing upload.")
                st.exception(e)

# ------------------ TAB 2: DAILY PROGRESS ------------------
with tab2:
    st.header("📊 Daily Progress")
    df = fetch_user_forms(user_id)

    if df.empty:
        st.info("No submissions yet.")
    else:
        df["form_date"] = pd.to_datetime(df["form_date"]).dt.date
        daily_steps = df.groupby("form_date")["form_stepcount"].sum().reset_index()
        total_steps = int(df["form_stepcount"].sum())
        today_steps = int(daily_steps[daily_steps["form_date"] == datetime.now().date()]["form_stepcount"].sum())
        days_participated = len(daily_steps)
        avg_steps = int(daily_steps["form_stepcount"].mean())
        distance_km = round(total_steps * 0.0008, 2)
        calories = int(total_steps * 0.04)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Steps", total_steps)
        c2.metric("Steps Today", today_steps)
        c3.metric("Days Participated", days_participated)

        c4, c5, c6 = st.columns(3)
        c4.metric("Avg Daily Steps", avg_steps)
        c5.metric("Total Distance (km)", distance_km)
        c6.metric("Total Calories Burned", calories)

        fig = px.bar(
            daily_steps,
            x="form_date",
            y="form_stepcount",
            title=f"{safe_username}'s Steps per Day",
            color_discrete_sequence=["#603494"],
            labels={"form_date": "Date", "form_stepcount": "Step Count"},
            template="plotly_white"
        )
        fig.update_xaxes(tickformat="%Y-%m-%d")
        st.plotly_chart(fig, use_container_width=True, config={"staticPlot": True})

        # --- Streak ---
        sorted_dates = sorted(daily_steps["form_date"])
        streak = 0
        if sorted_dates:
            streak = 1
            for i in range(len(sorted_dates) - 1, 0, -1):
                if (sorted_dates[i] - sorted_dates[i - 1]) == timedelta(days=1):
                    streak += 1
                else:
                    break
            if sorted_dates[-1] != datetime.now().date():
                streak = 0
        st.success(f"🔥 Current Streak: {streak} days" if streak else "No active streak.")

        # ------------------ EXPANDER: BADGES & ACHIEVEMENTS ------------------
        with st.expander("🏅 View Badges & Achievements", expanded=False):
            def calculate_badges(total_steps, streak):
                badges = []
                if total_steps >= 10000: badges.append("10K Steps")
                if total_steps >= 50000: badges.append("50K Steps")
                if total_steps >= 100000: badges.append("100K Steps")
                if streak >= 7: badges.append("7-Day Streak")
                if total_steps >= 200000: badges.append("Mo’ Legend")
                return badges

            def get_user_level(total_steps):
                if total_steps < 50000: return "🌱 Mo’ Rookie"
                elif total_steps < 150000: return "💪 Mo’ Pro"
                else: return "🏆 Mo’ Champion"

            badges = calculate_badges(total_steps, streak)
            level = get_user_level(total_steps)

            st.subheader("🎮 Your Rank")
            st.markdown(f"<h2 style='color:#603494;'>{level}</h2>", unsafe_allow_html=True)

            # Progress bar to next level
            level_thresholds = {"Mo’ Rookie": 0, "Mo’ Pro": 50000, "Mo’ Champion": 150000}
            next_level = "Mo’ Pro" if total_steps < 50000 else "Mo’ Champion" if total_steps < 150000 else None
            if next_level:
                progress = total_steps / level_thresholds[next_level]
                st.progress(min(progress, 1.0))
                st.info(f"🚀 {level_thresholds[next_level] - total_steps:,} steps to reach {next_level}!")
            else:
                st.success("🎉 You’re a Mo’ Champion! Keep inspiring others!")

            st.subheader("🏅 Your Badges")
            if badges:
                cols = st.columns(3)
                for i, badge in enumerate(badges):
                    cols[i % 3].success(f"✅ {badge}")
            else:
                st.info("No badges yet. Keep walking!")

            st.subheader("🔥 Challenges")
            challenges = []
            if today_steps < 10000:
                challenges.append(f"Hit 10,000 steps today! You’re at {today_steps:,}.")
            if streak < 7:
                challenges.append(f"Build a 7-day streak! Current: {streak} days.")
            if total_steps < 100000:
                challenges.append("Reach 100,000 steps milestone!")
            if not challenges:
                st.success("All challenges crushed! 🏆")
            else:
                for c in challenges:
                    st.write(f"- {c}")

# ------------------ FOOTER ------------------
carousel_msgs = [
    "💡 Movember Tip: Walking meetings are great for adding steps!",
    "🔥 Challenge: Hit 10,000 steps today!",
    "💪 DXC supports Movember — keep moving!"
]
st.markdown(f"<div class='footer-carousel'>{random.choice(carousel_msgs)}</div>", unsafe_allow_html=True)

# ------------------ HIDE STREAMLIT STYLE ELEMENTS TEST ------------------
st_html(
    """
    <script>
    window.addEventListener('load', () => {
        window.top.document.querySelectorAll(`[href*="streamlit.io"]`)
            .forEach(e => e.style.display = 'none');
    });
    </script>
    """,
    height=0,
)
