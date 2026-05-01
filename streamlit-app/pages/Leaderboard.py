import streamlit as st
import pandas as pd
import time
from db import supabase
import random
from pathlib import Path
from streamlit.components.v1 import html as st_html

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

st.set_page_config(page_title="🏆 Leaderboard", layout="wide", page_icon=logo_path2)

# Resolve logo path so it works from any page
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

# Check if file actually exists
if logo_path.exists():
    st.logo(str(logo_path), icon_image=str(logo_path), size="large")
else:
    st.warning(f"⚠️ Logo not found at: {logo_path}")

# ------------------ DXC BRANDING CSS ------------------
st.markdown("""
<style>
    /* White to Blue to Orange Gradient Background */
    .stApp {
        background: linear-gradient(135deg, 
            #FFFFFF 0%,     /* White */
            #F8FBFF 25%,    /* Light blue */
            #E3F2FD 50%,    /* Soft blue */
            #FFF3E0 75%,    /* Light orange */
            #FFE0B2 100%    /* Soft orange */
        );
        min-height: 100vh;
    }
    
    /* Make Streamlit header transparent */
    .stApp header {
        background: rgba(255, 255, 255, 0) !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    .header-container {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
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
    .stButton>button {
        background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
        color: white;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #6B94CB, #EF8A5C);
        transform: scale(1.05);
    }
    .footer-branding {
        text-align: center;
        font-size: 14px;
        color: #666;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 2px solid #7BA4DB;
    }
</style>
""", unsafe_allow_html=True)

# ------------------ HERO HEADER ------------------
header_html = """
<div class="header-container">
    <div>
        <div class="header-title">🏆 DXC Step Leaderboard</div>
        <div class="header-subtitle">Track the leaders and keep moving!</div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ------------------ SECURITY: LOGIN CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username", "Guest")

# ------------------ FILTERS ------------------
st.subheader("Filter Leaderboard")

col1, col2 = st.columns(2)
with col1:
    selected_date = st.date_input(
        "Select a date (leave empty for all-time)",
        value=None
    )
with col2:
    view_option = st.selectbox(
        "Show:",
        ["All", "Top 10", "Bottom 10"]
    )

# ------------------ FETCH DATA FROM SUPABASE ------------------
try:
    forms_query = supabase.table("forms").select("user_id, form_stepcount, form_date")
    if selected_date:
        forms_query = forms_query.eq("form_date", str(selected_date))
    forms = forms_query.execute().data
except Exception as e:
    st.error(f"Database error while fetching forms: {e}")
    st.stop()

if not forms:
    st.info("No step data available for the selected date." if selected_date else "No step data available.")
    st.stop()

df = pd.DataFrame(forms)

# ------------------ AGGREGATE STEPS SECURELY ------------------
try:
    step_summary = df.groupby("user_id")["form_stepcount"].sum().reset_index()
    step_summary.rename(columns={"form_stepcount": "total_steps"}, inplace=True)
except Exception as e:
    st.error(f"Error processing step data: {e}")
    st.stop()

# ------------------ GET USERNAMES ------------------
try:
    users = supabase.table("users").select("user_id, user_name").execute().data
    users_df = pd.DataFrame(users)
except Exception as e:
    st.error(f"Error fetching user data, please try again later.")
    st.stop()

# Merge steps with usernames
leaderboard = pd.merge(step_summary, users_df, on="user_id", how="inner")
leaderboard = leaderboard[["user_name", "total_steps"]]


leaderboard.rename(columns={
    "user_name": "Username",
    "total_steps": "Step Count"
}, inplace=True)

# ------------------ SORTING OPTIONS ------------------
if view_option == "Top 10":
    leaderboard = leaderboard.sort_values("Step Count", ascending=False).head(10)
elif view_option == "Bottom 10":
    leaderboard = leaderboard.sort_values("Step Count", ascending=True).head(10)
else:  # All
    leaderboard = leaderboard.sort_values("Step Count", ascending=False)

leaderboard.reset_index(drop=True, inplace=True)
leaderboard.index += 1  # Start rank from 1

# ------------------ DISPLAY ------------------
st.subheader("Leaderboard")
if selected_date:
    st.caption(f"Showing results for **{selected_date}**")
else:
    st.caption("Showing **all-time** results")

if leaderboard.empty:
    st.info("No data available to display.")
else:
    st.dataframe(leaderboard, width="stretch")

    # Highlight top performer (only for All or Top 10 views)
    if view_option != "Bottom 10" and not leaderboard.empty:
        top_user = leaderboard.iloc[0]
        st.success(f"🥇 {top_user['Username']} is leading with {int(top_user['Step Count'])} steps!")

# ------------------ SIDEBAR ------------------
st.sidebar.markdown(f"<h3 style='color:#7BA4DB;'>Welcome, {username}!</h3>", unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# ------------------ FOOTER ------------------
st.markdown(
    "<div class='footer-branding' style='text-align:center; font-weight:bold; margin-top:40px; padding-top:20px; border-top:2px solid #7BA4DB;'>DXC Technology</div>",
    unsafe_allow_html=True
)

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