import streamlit as st
import os
import shutil
import zipfile
import io
import pandas as pd
from db import supabase

# ------------------ LOGIN & ROLE CHECK ------------------
if not st.session_state.get("logged_in"):
    st.warning("Please log in first.")
    st.stop()

username = st.session_state.get("username", "")
user_resp = supabase.table("users").select("user_admin").eq("user_name", username).limit(1).execute()
if not user_resp.data or not user_resp.data[0].get("user_admin", False):
    st.error("Access denied: Admins only.")
    st.stop()

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("🔐 Admin Dashboard")
st.write("Manage data and access evidence folder.")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize session state
if "confirm_delete" not in st.session_state:
    st.session_state["confirm_delete"] = None
if "confirm_clear" not in st.session_state:
    st.session_state["confirm_clear"] = False

# ------------------ FETCH DATA FROM SUPABASE ------------------
def fetch_all_submissions():
    forms = supabase.table("forms") \
        .select("*") \
        .eq("form_verified", False) \
        .gt("form_stepcount", 15000) \
        .execute().data
    users = supabase.table("users").select("user_id, user_name").execute().data
    if not forms:
        return pd.DataFrame()
    df_forms = pd.DataFrame(forms)
    df_users = pd.DataFrame(users)
    return pd.merge(df_forms, df_users, on="user_id")

df = fetch_all_submissions()

# ------------------ CONFIRM DELETE ------------------
if st.session_state["confirm_delete"] is not None and not df.empty:
    confirm_idx = st.session_state["confirm_delete"]
    if confirm_idx in df.index:
        confirm_row = df.loc[confirm_idx]
        st.warning(f"Are you sure you want to delete submission for **{confirm_row['user_name']}** on **{confirm_row['form_date']}**?")
        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Yes, Delete"):
                try:
                    supabase.table("forms").delete().eq("form_id", confirm_row["form_id"]).execute()
                    file_path = os.path.join(UPLOAD_FOLDER, confirm_row["form_filepath"])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    st.error(f"Error deleting submission: {e}")
                st.session_state["confirm_delete"] = None
                st.rerun()
        with colB:
            if st.button("❌ Cancel"):
                st.session_state["confirm_delete"] = None
                st.rerun()

# ------------------ 1. HIGH-STEP SUBMISSIONS (>15,000) ------------------
st.subheader("📊 Unverified Submissions (Steps > 15,000)")
if not df.empty:
    for idx, row in df.iterrows():
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            file_path = os.path.join(UPLOAD_FOLDER, row["form_filepath"])
            if os.path.exists(file_path):
                st.image(file_path, width=100)
        with col2:
            st.markdown(f"**Name:** {row['user_name']} | **Date:** {row['form_date']} | **Steps:** {row['form_stepcount']}")
            with st.expander("View Full Screenshot"):
                if os.path.exists(file_path):
                    st.image(file_path, caption=f"Screenshot for {row['user_name']}", use_container_width=True)
                else:
                    st.warning("Screenshot not found.")
        with col3:
            if st.button("✅ Verify", key=f"dismiss_{idx}"):
                try:
                    supabase.table("forms") \
                        .update({"form_verified": True}) \
                        .eq("form_id", row["form_id"]) \
                        .execute()
                    st.success(f"Verified submission for {row['user_name']}")
                except Exception as e:
                    st.error(f"Error verifying form: {e}")
                st.rerun()
            if st.button("❌ Delete", key=f"delete_{idx}"):
                st.session_state["confirm_delete"] = idx
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
st.warning("This will permanently delete ALL submissions and screenshots. This action cannot be undone.")
if not st.session_state["confirm_clear"]:
    if st.button("Clear All Data"):
        st.session_state["confirm_clear"] = True
        st.rerun()
else:
    st.error("Are you sure you want to clear ALL data? This will remove all DB records and uploaded screenshots.")
    colA, colB = st.columns(2)
    with colA:
        if st.button("✅ Yes, Clear Everything"):
            try:
                supabase.table("forms").delete().neq("form_id", 0).execute()
                if os.path.exists(UPLOAD_FOLDER):
                    shutil.rmtree(UPLOAD_FOLDER)
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                st.success("✅ All data cleared successfully!")
            except Exception as e:
                st.error(f"Error clearing data: {e}")
            st.session_state["confirm_clear"] = False
            st.rerun()
    with colB:
        if st.button("❌ Cancel"):
            st.session_state["confirm_clear"] = False
            st.rerun()