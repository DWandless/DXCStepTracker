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
import bcrypt
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome,
                        hide_streamlit_branding, check_login_required, handle_logout, secure_filename)

# ------------------ PAGE CONFIG ------------------
logo_path = Path(__file__).resolve().parents[1] / "assets" / "logo.png"
st.set_page_config(page_title="Admin Dashboard", layout="wide", page_icon=logo_path)

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logo(Path(__file__).resolve().parents[1])
render_header("Admin Dashboard", "Manage submissions and verify evidence.")

# ------------------ LOGIN & ROLE CHECK ------------------
username = check_login_required()
user_resp = supabase.table("users").select("user_admin").eq("user_name", username).limit(1).execute()
if not user_resp.data or not user_resp.data[0].get("user_admin", False):
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
        .gt("form_stepcount", 9999) \
        .execute().data
    users = supabase.table("users").select("user_id, user_name").execute().data
    if not forms:
        return pd.DataFrame()
    df_forms = pd.DataFrame(forms)
    df_users = pd.DataFrame(users)
    return pd.merge(df_forms, df_users, on="user_id")

df = fetch_all_submissions()

# ------------------ SIMPLE CONFIRM DELETE (CSS-RESISTANT) ------------------
# Show a minimal confirmation widget when a pending delete is set.
if st.session_state["pending_delete"]:
    pd = st.session_state["pending_delete"]
    st.markdown("---")
    st.error(f"### Confirm Deletion")
    st.markdown(f"You are about to permanently delete the submission for:")
    st.markdown(f"- **User:** {pd['user_name']}")
    st.markdown(f"- **Date:** {pd['form_date']}")
    st.markdown(f"- **Steps:** {pd.get('steps', 'N/A')}")
    st.markdown("")
    confirm_cb = st.checkbox("⚠ I understand this action cannot be undone", key="confirm_delete_cb")
    st.markdown("")
    colA, colB, colC = st.columns([1, 1, 2])
    with colA:
        if st.button("🗙 Delete Permanently", disabled=not confirm_cb, type="secondary"):
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
        if st.button("Cancel", key="cancel_delete_btn", type="secondary"):
            st.session_state["pending_delete"] = None
            st.rerun()
    st.markdown("---")

# ------------------ SIDEBAR ------------------
if render_sidebar_welcome(username):
    handle_logout()

# ------------------ 1. HIGH-STEP SUBMISSIONS (>10,000) ------------------
st.subheader(
    "Unverified Submissions (Steps > 10,000)",
    help="Review and verify step submissions over 10,000 steps. Check the screenshot evidence and click 'Verify' to approve or 'Delete' to remove suspicious entries."
)

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
            if st.button("Verify", key=f"verify_{idx}"):
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
            if st.button("Delete", key=f"delete_{idx}"):
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
    st.warning("This will permentantly delete ALL form submissions and uploaded screenshots. This action cannot be undone.")

    # --- RE-AUTHENTICATION STEP ---
    with st.form("reauth_form"):
        admin_password = st.text_input("Re-enter your password to confirm:", type="password")
        submitted = st.form_submit_button("Confirm and Delete")

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
                            st.success("All data cleared successfully!")
                        except Exception:
                            st.error("Error clearing data. Please check logs.")
                    else:
                        st.error("Invalid password. Re-authentication failed.")
                else:
                    st.error("Could not verify admin identity.")
            except Exception:
                st.error("Error verifying credentials.")

    # --- Cancel button OUTSIDE the form ---
    if st.button("Cancel", key="cancel_clear_btn"):
        st.session_state["confirm_clear"] = False
        st.rerun()

# ------------------ FOOTER ------------------
render_footer()
hide_streamlit_branding()
