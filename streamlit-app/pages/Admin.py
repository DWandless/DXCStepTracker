import streamlit as st
import os
import shutil
import zipfile
import io
import pandas as pd
import re
import unicodedata
import time
from db import supabase
import random
import bcrypt
from pathlib import Path
from streamlit.components.v1 import html as st_html

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parents[1] / "assets" / "logo3.png"

st.set_page_config(page_title="🔐 Admin Dashboard", layout="wide", page_icon=logo_path2)

# Add a top logo in sidebar before Streamlit’s nav
# Resolve logo path dynamically

# Resolve logo path so it works from any page
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"

# Check if file actually exists
if logo_path.exists():
    st.logo(str(logo_path), icon_image=str(logo_path), size="large")
else:
    st.warning(f"⚠️ Logo not found at: {logo_path}")

# ------------------ DXC BRANDING & MOVEMBER CSS ------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #FFFFFF;
    }
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
header_html = """
<div class="header-container">
    <div>
        <div class="header-title">🔐 Admin Dashboard</div>
        <div class="header-subtitle">Manage submissions, verify evidence, and maintain the challenge securely.</div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ------------------ LOGIN & ROLE CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username", "")
user_resp = supabase.table("users").select("user_admin").eq("user_name", username).limit(1).execute()
if not user_resp.data or not user_resp.data[0].get("user_admin", False):
    st.error("Access denied: Admins only.")
    st.stop()

# ------------------ SECURITY FUNCTION ------------------
def secure_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filenames to prevent directory traversal or injection."""
    if not filename:
        return "file"
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9.\-_]", "_", filename)
    return filename[:max_length]

# ------------------ CONFIG & STATE ------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# replace old confirm state with a simpler pending_delete entry
if "pending_delete" not in st.session_state:
    st.session_state["pending_delete"] = None
if "confirm_clear" not in st.session_state:
    st.session_state["confirm_clear"] = False

# ------------------ FETCH DATA FROM SUPABASE ------------------
def fetch_all_submissions():
    forms = supabase.table("forms") \
        .select("*") \
        .eq("form_verified", False) \
        .gt("form_stepcount", 9999) \
        .execute().data
    users = supabase.table("users").select("user_id, user_name").execute().data
    if not forms:
        return pd.DataFrame()
    df_forms = pd.DataFrame(forms)
    df_users = pd.DataFrame(users)
    return pd.merge(df_forms, df_users, on="user_id")

df = fetch_all_submissions()

# ------------------ DELETE BUTTON TRIGGERING MODAL ------------------
if st.session_state.get("pending_delete"):
    pd = st.session_state["pending_delete"]

    # Main delete trigger button
    if st.button(f"🗑️ Delete submission for {pd['user_name']}"):
        
        # Open a modal popup
        with st.modal("confirm_delete_modal", title="Confirm Deletion"):
            st.write(f"⚠️ Are you sure you want to permanently delete the submission for **{pd['user_name']}** on **{pd['form_date']}**?")

            colA, colB = st.columns(2)
            with colA:
                if st.button("✅ Yes, Delete"):
                    try:
                        # Delete from database
                        supabase.table("forms").delete().eq("form_id", pd["form_id"]).execute()

                        # Delete uploaded file if exists
                        safe_name = secure_filename(os.path.basename(str(pd.get("file", ""))))
                        file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                        if os.path.exists(file_path):
                            os.remove(file_path)

                        st.success("Submission deleted successfully!")
                    except Exception:
                        st.error("Error deleting submission.")
                    
                    # Clear pending delete and close modal
                    st.session_state["pending_delete"] = None
                    st.experimental_rerun()

            with colB:
                if st.button("❌ Cancel"):
                    st.session_state["pending_delete"] = None
                    st.experimental_rerun()

# ------------------ SIDEBAR ------------------
st.sidebar.markdown(f"<h3 style='color:#603494;'>Welcome, {username}!</h3>", unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# ------------------ 1. HIGH-STEP SUBMISSIONS (>10,000) ------------------
st.subheader("📊 Unverified Submissions (Steps > 10,000)")

if not df.empty:
    for idx, row in df.iterrows():
        col1, col2, col3 = st.columns([1, 3, 2])
        safe_name = secure_filename(os.path.basename(str(row.get("form_filepath", ""))))
        file_path = os.path.join(UPLOAD_FOLDER, safe_name)

        with col1:
            if os.path.exists(file_path):
                st.image(file_path, width=100)
            else:
                st.warning("No preview available.")

        with col2:
            st.markdown(f"**Name:** {row['user_name']} | **Date:** {row['form_date']} | **Steps:** {row['form_stepcount']}")
            with st.expander("View Full Screenshot"):
                if os.path.exists(file_path):
                    st.image(file_path, caption=f"Screenshot for {row['user_name']}", width="stretch")
                else:
                    st.warning("Screenshot not found.")

        with col3:
            if st.button("✅ Verify", key=f"verify_{idx}"):
                try:
                    supabase.table("forms") \
                        .update({"form_verified": True}) \
                        .eq("form_id", row["form_id"]) \
                        .execute()

                    # Delete the image from uploads after verification, not needed anymore
                    try:
                        os.remove(file_path)
                    except FileNotFoundError:
                        pass

                except Exception as e:
                    st.error(f"Error verifying form, please try again later.")
                st.rerun()
            if st.button("❌ Delete", key=f"delete_{idx}"):
                # set a small pending_delete dict rather than relying on index
                st.session_state["pending_delete"] = {
                    "form_id": row["form_id"],
                    "user_name": row["user_name"],
                    "form_date": row["form_date"],
                    "file": row.get("form_filepath", "")
                }
                st.rerun()
        st.markdown("---")
else:
    st.info("No high-step unverified submissions found.")

# ------------------ 2. DOWNLOAD STEP DATA ------------------
st.subheader("📥 Download Step Data")
if not df.empty:
    csv_data = df.to_csv(index=False)
    st.download_button("Download Step Data CSV", csv_data, file_name="step_data.csv")
else:
    st.info("No step data available.")

# ------------------ 3. EVIDENCE FOLDER ------------------
st.subheader("📂 Evidence Folder")
folder_path = os.path.abspath(UPLOAD_FOLDER)
st.markdown(f"Path: `{folder_path}`")

if os.path.exists(UPLOAD_FOLDER) and os.listdir(UPLOAD_FOLDER):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for root, _, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)
    zip_buffer.seek(0)
    st.download_button("Download All Evidence as ZIP", zip_buffer, file_name="evidence.zip")
else:
    st.info("No evidence files found.")


# ------------------ 4. RESET CHALLENGE DATA ------------------
st.subheader("⚠️ Reset Challenge Data")

if not st.session_state.get("confirm_clear"):
    if st.button("Clear All Data"):
        st.session_state["confirm_clear"] = True
        st.rerun()
else:
    st.warning("This will permentantly delete ALL form submissions and uploaded screenshots. This action cannot be undone.")

    # --- RE-AUTHENTICATION STEP ---
    with st.form("reauth_form"):
        admin_password = st.text_input("Re-enter your password to confirm:", type="password")
        submitted = st.form_submit_button("✅ Confirm and Delete")

        if submitted:
            try:
                # Get stored password hash
                resp = supabase.table("users").select("user_password").eq("user_name", username).limit(1).execute()
                if resp.data:
                    stored_hash = resp.data[0]["user_password"].encode("utf-8")
                    if bcrypt.checkpw(admin_password.encode("utf-8"), stored_hash):
                        # Auth OK — proceed with deletion
                        try:
                            supabase.table("forms").delete().neq("form_id", 0).execute()
                            if os.path.exists(UPLOAD_FOLDER):
                                shutil.rmtree(UPLOAD_FOLDER)
                                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            st.success("✅ All data cleared successfully!")
                        except Exception:
                            st.error("Error clearing data. Please check logs.")
                    else:
                        st.error("Invalid password. Re-authentication failed.")
                else:
                    st.error("Could not verify admin identity.")
            except Exception:
                st.error("Error verifying credentials.")

    # --- Cancel button OUTSIDE the form ---
    if st.button("❌ Cancel"):
        st.session_state["confirm_clear"] = False
        st.rerun()

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

# Show one random message per page load
carousel_placeholder = st.empty()
msg = random.choice(carousel_messages)
carousel_placeholder.markdown(
    f"<div class='footer-carousel'>{msg}</div>",
    unsafe_allow_html=True
)

# Render branding once (static)
st.markdown(
    "<div class='footer-branding' style='color:#603494; text-align:center; font-weight:bold; margin-top:20px;'>DXC Technology | Movember 2025</div>",
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
