import streamlit as st
import os
import shutil
import zipfile
import io
import pandas as pd
import re
import unicodedata
import time
from pathlib import Path
from db import supabase
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome,
                        hide_streamlit_branding, check_login_required, handle_logout, secure_filename)
from onedrive_storage import get_file_download_url, delete_from_onedrive, get_access_token

# ------------------ PAGE CONFIG ------------------
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Admin Dashboard", layout="wide", page_icon=logo_path)

# Hide branding early
hide_streamlit_branding()

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("Admin Dashboard", "Manage submissions and verify evidence.")

# ------------------ LOGIN & ROLE CHECK ------------------
username = check_login_required()
user_email = st.session_state.get("user_email", "")

# Check if user email is in admin list from secrets
admin_emails = st.secrets.get("ADMIN_EMAILS", [])
if user_email.lower() not in [email.lower() for email in admin_emails]:
    st.error("Access denied: Admins only.")
    st.stop()

# ------------------ SECURITY FUNCTION ------------------
# secure_filename now imported from components

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
        .gt("form_stepcount", 19999) \
        .execute().data
    users = supabase.table("users").select("user_id, user_name").execute().data
    if not forms:
        return pd.DataFrame()
    df_forms = pd.DataFrame(forms)
    df_users = pd.DataFrame(users)
    return pd.merge(df_forms, df_users, on="user_id")

df = fetch_all_submissions()

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome():
    handle_logout()

# ------------------ 1. HIGH-STEP SUBMISSIONS (>20,000) ------------------
st.subheader(
    "Unverified Submissions (Steps > 20,000)",
    help="Review and verify step submissions over 20,000 steps. Check the screenshot evidence and click 'Verify' to approve or 'Delete' to remove suspicious entries."
)

if not df.empty:
    for idx, row in df.iterrows():
        col1, col2, col3 = st.columns([1, 3, 2])
        filepath = row.get("form_filepath", "")
        
        # Check if it's a OneDrive URL or local file
        is_onedrive = filepath.startswith("http") or "sharepoint" in filepath.lower() or "onedrive" in filepath.lower()
        
        with col1:
            if is_onedrive:
                st.markdown("[📁 View in OneDrive](" + filepath + ")")
            else:
                safe_name = secure_filename(os.path.basename(str(filepath)))
                file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                if os.path.exists(file_path):
                    st.image(file_path, width=100)
                else:
                    st.warning("No preview available.")

        with col2:
            st.markdown(f"**Name:** {row['user_name']} | **Date:** {row['form_date']} | **Steps:** {row['form_stepcount']}")
            with st.expander("View Full Screenshot"):
                if is_onedrive:
                    st.markdown(f"**Evidence stored in OneDrive**")
                    st.markdown(f"[🔗 Open in OneDrive]({filepath})")
                    st.info("Click the link above to view the screenshot in OneDrive.")
                else:
                    safe_name = secure_filename(os.path.basename(str(filepath)))
                    file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                    if os.path.exists(file_path):
                        st.image(file_path, caption=f"Screenshot for {row['user_name']}", width="stretch")
                    else:
                        st.warning("Screenshot not found.")

        with col3:
            if st.button("Verify", key=f"verify_{idx}"):
                try:
                    supabase.table("forms") \
                        .update({"form_verified": True}) \
                        .eq("form_id", row["form_id"]) \
                        .execute()

                    # Delete the image after verification
                    if not is_onedrive:
                        # Local file - delete from uploads folder
                        try:
                            safe_name = secure_filename(os.path.basename(str(filepath)))
                            file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                            os.remove(file_path)
                        except FileNotFoundError:
                            pass
                    # Note: OneDrive files are kept for records

                except Exception as e:
                    st.error(f"Error verifying form, please try again later.")
                st.rerun()
            if st.button("Delete", key=f"delete_{idx}"):
                # set a small pending_delete dict rather than relying on index
                st.session_state["pending_delete"] = {
                    "form_id": row["form_id"],
                    "user_name": row["user_name"],
                    "form_date": row["form_date"],
                    "form_stepcount": row["form_stepcount"],
                    "file": row.get("form_filepath", "")
                }
                st.rerun()
        
        # Show confirmation dialog inline if this row is being deleted
        if st.session_state["pending_delete"] and st.session_state["pending_delete"]["form_id"] == row["form_id"]:
            pd = st.session_state["pending_delete"]
            st.error("### ⚠ Confirm Deletion")
            st.markdown(f"You are about to permanently delete the submission for:")
            st.markdown(f"- **User:** {pd['user_name']}")
            st.markdown(f"- **Date:** {pd['form_date']}")
            st.markdown(f"- **Steps:** {pd['form_stepcount']}")
            st.markdown("")
            confirm_cb = st.checkbox("I understand this action cannot be undone", key="confirm_delete_cb")
            st.markdown("")
            colA, colB, colC = st.columns([1, 1, 2])
            with colA:
                if st.button("🗙 Delete Permanently", disabled=not confirm_cb, type="secondary", key=f"confirm_delete_{idx}"):
                    try:
                        supabase.table("forms").delete().eq("form_id", pd["form_id"]).execute()
                        safe_name = secure_filename(os.path.basename(str(pd.get("file", ""))))
                        file_path = os.path.join(UPLOAD_FOLDER, safe_name)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        st.success("Submission deleted successfully!")
                    except Exception:
                        st.error("Error deleting submission.")
                    st.session_state["pending_delete"] = None
                    st.rerun()
            with colB:
                if st.button("Cancel", key=f"cancel_delete_{idx}", type="secondary"):
                    st.session_state["pending_delete"] = None
                    st.rerun()
        
        st.markdown("---")
else:
    st.info("No high-step unverified submissions found.")

# ------------------ 2. DOWNLOAD STEP DATA ------------------
st.subheader(
    "Download Step Data",
    help="Export all step submission data as a CSV file for analysis, reporting, or backup purposes."
)
if not df.empty:
    csv_data = df.to_csv(index=False)
    st.download_button("Download Step Data CSV", csv_data, file_name="step_data.csv")
else:
    st.info("No step data available.")

# ------------------ 3. EVIDENCE FOLDER ------------------
st.subheader(
    "Evidence Folder",
    help="Download all uploaded screenshot evidence as a ZIP file for archival or review purposes."
)
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
st.subheader(
    "Reset Challenge Data",
    help="Danger Zone: This will permanently delete ALL step submissions and uploaded screenshots from the database. Use this only to reset the challenge or clear test data."
)
st.error("⚠ Warning: This action will delete all data and cannot be undone!")

if not st.session_state.get("confirm_clear"):
    if st.button("Clear All Data"):
        st.session_state["confirm_clear"] = True
        st.rerun()
else:
    st.warning("This will permanently delete ALL form submissions and uploaded screenshots. This action cannot be undone.")
    
    # Confirmation checkbox
    confirm_checkbox = st.checkbox("⚠ I understand this action is permanent and cannot be undone")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Confirm and Delete All Data", type="primary", disabled=not confirm_checkbox):
            try:
                supabase.table("forms").delete().neq("form_id", 0).execute()
                if os.path.exists(UPLOAD_FOLDER):
                    shutil.rmtree(UPLOAD_FOLDER)
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                st.success("All data cleared successfully!")
                st.session_state["confirm_clear"] = False
            except Exception as e:
                st.error(f"Error clearing data: {str(e)}")
    
    with col2:
        if st.button("Cancel", key="cancel_clear_btn"):
            st.session_state["confirm_clear"] = False
            st.rerun()

# ------------------ FOOTER (ALWAYS RENDER) ------------------
render_footer()
