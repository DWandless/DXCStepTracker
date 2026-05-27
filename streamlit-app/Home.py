import streamlit as st
import os
import logging
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
from PIL import Image, UnidentifiedImageError
import re, unicodedata, random, io, time
import hashlib
from pathlib import Path
from authlib.integrations.base_client.errors import OAuthError
from requests_oauthlib import OAuth2Session
from db import supabase
from components import (apply_dxc_theme, setup_logo, render_header, render_footer, render_sidebar_welcome,
                        hide_streamlit_branding, secure_filename, get_user_id, fetch_user_forms, render_sidebar_welcome, handle_logout, log_audit_event, get_met_values, setup_logging)
from onedrive_storage import upload_to_onedrive, get_access_token

# ------------------ PAGE CONFIG ------------------
logo_path2 = Path(__file__).resolve().parent / ".streamlit" / "static" / "assets" / "logo.png"
st.set_page_config(page_title="DXC Step Tracker", layout="wide", page_icon=logo_path2)

# Hide branding early
hide_streamlit_branding()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

# ------------------ APPLY THEME & LOGO ------------------
apply_dxc_theme()
setup_logging()
setup_logo()
render_header("DXC Step Tracker", "Keep Moving and Track your steps better!")

# ------------------ AZURE OAUTH CONFIG ------------------
azure = st.secrets["azure"]
CLIENT_ID = azure["client_id"]
CLIENT_SECRET = azure["client_secret"]
TENANT_ID = azure.get("tenant_id", "93f33571-550f-43cf-b09f-cd331338d086")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_URL = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_URL = f"{AUTHORITY}/oauth2/v2.0/token"
REDIRECT_URI = "https://dxcsteptracker.streamlit.app/"

oauth = OAuth2Session(
    client_id=CLIENT_ID,
    scope=["openid", "profile", "email", "User.Read", "Files.ReadWrite", "Files.ReadWrite.AppFolder"],
    redirect_uri=REDIRECT_URI,
)

# ------------------ SESSION DEFAULTS ------------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "display_name" not in st.session_state:
    st.session_state["display_name"] = ""
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

# ------------------ LOGIN UTILITIES ------------------
def standardize_name(name):
    """Convert name from 'last, first' format to 'first last' format."""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def is_token_expired(token):
    """Check if JWT token is expired."""
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get("exp")
        if exp:
            import time
            return time.time() >= exp
        return False
    except Exception:
        return True

def get_or_create_user(email, display_name):
    """Get existing user or create new user in database, return formatted name."""
    try:
        result = supabase.table("users").select("user_id, user_name").eq("user_email", email).execute()
        
        if result.data:
            return result.data[0]["user_name"]
        else:
            standardized_name = standardize_name(display_name)
            supabase.table("users").insert({
                "user_email": email,
                "user_name": standardized_name,
            }).execute()
            logging.info(f"New user created: {email[:3]}***@*** ({standardized_name})")
            return standardized_name
    except Exception as e:
        logging.error(f"Database error in get_or_create_user: {e}")
        return standardize_name(display_name)

# ------------------ HANDLE OAUTH REDIRECT ------------------
query_params = st.query_params

if "code" in query_params and st.session_state["token"] is None:
    try:
        token = oauth.fetch_token(
            token_url=TOKEN_URL,
            code=query_params["code"],
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        st.session_state["token"] = token
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        error_str = str(e)
        if "AADSTS70008" in error_str or "expired" in error_str.lower():
            st.error("Session timed out. Please log in again.")
        else:
            st.error(f"Authentication failed: {error_str[:200]}")

# ------------------ LOGIN FLOW ------------------
token = st.session_state["token"]

if token:
    token_to_check = token.get("id_token") or token.get("access_token")
    if token_to_check and is_token_expired(token_to_check):
        st.error("Session expired. Please log in again.")
        if st.button("Log In Again"):
            st.session_state.clear()
            st.rerun()
    
    try:
        import jwt
        token_to_decode = token.get("id_token") or token.get("access_token")
        
        if not token_to_decode:
            st.error("Authentication failed. Please try again.")
            if st.button("Try Again"):
                st.session_state.clear()
                st.rerun()
        else:
            decoded = jwt.decode(token_to_decode, options={"verify_signature": False})
            user_email = decoded.get("preferred_username") or decoded.get("email") or decoded.get("upn") or decoded.get("unique_name") or ""
            user_name_raw = decoded.get("name", "Unknown User")
            
            if "," in user_name_raw:
                last, first = [x.strip() for x in user_name_raw.split(",", 1)]
                user_name = f"{first} {last}"
            else:
                user_name = user_name_raw.strip()
            
            if not st.session_state.logged_in:
                username = get_or_create_user(user_email, user_name)
                st.session_state.logged_in = True
                st.session_state.username = user_email
                st.session_state.display_name = username
                st.session_state.user_email = user_email
                st.session_state.login_time = datetime.now().timestamp()
                logging.info(f"User logged in: {username} ({user_email[:3]}***@***)")
                st.rerun()
    except Exception as e:
        st.error(f"Error processing authentication: {e}")
        if st.button("Try Again"):
            st.session_state.clear()
            st.rerun()

# ------------------ SHOW LOGIN UI IF NOT LOGGED IN ------------------
if not st.session_state.logged_in:
    st.markdown("---")
    st.subheader("Sign In")
    st.caption("Log in with your Microsoft account to track your steps and participate in challenges.")
    
    auth_url, _ = oauth.authorization_url(
        AUTHORIZE_URL,
        prompt="select_account",
    )
    
    st.link_button("Sign in with Microsoft", auth_url, type="primary", use_container_width=True)
    
    render_footer()
    st.stop()

# ------------------ HELPERS ------------------
# Utility functions now imported from components

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

# ------------------ USER SETUP (LOGGED IN) ------------------
username = st.session_state.get("username")  # This is the email
user_email = username  # For audit logging
user_id = get_user_id(username)
if not user_id:
    st.error("User not found.")
    st.stop()

# Get user's name for filename generation
try:
    user_data = supabase.table("users").select("user_name").eq("user_id", user_id).execute()
    user_name = user_data.data[0]["user_name"] if user_data.data else username
    safe_username = secure_filename(user_name)
except Exception:
    safe_username = secure_filename(username.split("@")[0])  # Fallback to email prefix

if render_sidebar_welcome():
    handle_logout()

# ------------------ TABS ------------------
tab1, tab2, tab3, tab4 = st.tabs(["✚ Submit Steps", "✦ AI & Wellbeing Challenges",  "➜ Daily Progress", "⚑ Teams"])

# ------------------ TAB 1: SUBMIT STEPS ------------------
with tab1:
    st.header("✚ Submit Your Steps")
    st.caption("Log your daily step count with screenshot proof.")
    
    # Previous button - commented out
    # st.link_button(
    #     "Didn't do a step-based activity? - Convert your activity to steps here",
    #     "https://teams.microsoft.com/l/app/?titleId=T_6a6c4d51-8b71-4883-827a-cb941f371364",
    #     type="secondary"
    # )
    
    with st.expander("Convert non-walking activities to steps"):
        st.caption("Instant conversion based on MET (Metabolic Equivalent) values.")
        
        # Load MET values from JSON file
        met_values = get_met_values()
        
        if not met_values:
            st.error("Unable to load activity data. Please try again later.")
        
        activity_col, time_col = st.columns(2)
        with activity_col:
            selected_activity = st.selectbox("Select Activity", sorted(met_values.keys()))
        
        with time_col:
            duration_minutes = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=30, step=5)
        
        # Calculate steps
        steps_per_minute = met_values[selected_activity]
        calculated_steps = int(steps_per_minute * duration_minutes)
        
        st.success(f"Estimated steps: **{calculated_steps:,}**")
        st.caption(f"Based on {steps_per_minute} steps per minute for {selected_activity}")
        
        if st.button("Use this step count", type="secondary"):
            st.session_state.auto_fill_steps = calculated_steps
            st.rerun()
    
    with st.form("step_submission_form", clear_on_submit=True):
        date_col, step_col = st.columns(2)
        with date_col: 
            step_date = st.date_input(
                "Date",
                min_value=date(2026, 5, 14),
                max_value=date(2026, 6, 11),
                value=date.today(),
                help="Select the date when you recorded these steps. Valid dates: 14/05/26 to 11/06/26."
            )
        with step_col: 
            default_steps = st.session_state.get("auto_fill_steps", 0)
            steps = st.number_input(
                "Step Count", 
                min_value=0, 
                step=100,
                value=default_steps,
                help="Enter the total number of steps you walked on this date (1-100,000)."
            )
        screenshot = st.file_uploader(
            "Upload Screenshot (PNG/JPG) - Required for 20,000+ steps", 
            type=["png", "jpg", "jpeg"],
            help="Upload a screenshot from your fitness tracker or step counter app as proof. Required for submissions 20,000+ steps. By uploading, you agree to share this data within the organization."
        )

        if screenshot:
            if screenshot.size > MAX_UPLOAD_SIZE:
                st.error("File too large. Max 5 MB."); st.stop()
            try:
                img = Image.open(screenshot)
            except UnidentifiedImageError:
                st.error("Invalid image."); st.stop()

        submitted = st.form_submit_button("Submit", type="secondary")
        if submitted:
            now = datetime.now()
            last_submission = st.session_state.get("last_submission_time") or get_last_submission_time(user_id)

            # --- 30-second cooldown check ---
            if last_submission and now - last_submission < timedelta(seconds=30):
                remaining = timedelta(seconds=30) - (now - last_submission)
                minutes, seconds = divmod(remaining.total_seconds(), 60)
                st.warning(f"Please wait {int(seconds)}s before submitting again.")
            elif steps <= 0 or steps > 100000:
                st.error("Enter a valid step count (1–100,000).")
            elif steps >= 20000 and not screenshot:
                st.error("Screenshot required for submissions 20,000+ steps.")
            else:
                # --- Daily submission limit check (10 per day) ---
                try:
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    daily_submissions = supabase.table("forms") \
                        .select("form_id") \
                        .eq("user_id", user_id) \
                        .gte("form_created_at", today_start.isoformat()) \
                        .execute()
                    
                    submission_count = len(daily_submissions.data) if daily_submissions.data else 0
                    
                    if submission_count >= 10:
                        st.error("Daily submission limit reached (10 per day). Please try again tomorrow.")
                        log_audit_event("RATE_LIMIT_EXCEEDED", user_email, f"Daily limit: {submission_count}/10")
                        st.stop()
                except Exception as e:
                    logging.error(f"Error checking daily submission limit: {e}")
                    # Proceed with submission if check fails
                
                try:
                    file_url = None
                    
                    # Only process image if screenshot was provided
                    if screenshot:
                        img = Image.open(screenshot).convert("RGB")
                        filename = secure_filename(f"{safe_username}_{step_date}_{datetime.now().strftime('%H%M%S')}.jpg")
                        
                        # Convert image to bytes
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format="JPEG", quality=85, optimize=True)
                        img_bytes = img_byte_arr.getvalue()
                        
                        # For steps >= 20,000, upload to OneDrive
                        if steps >= 20000:
                            access_token = get_access_token()
                            
                            if access_token:
                                upload_result = upload_to_onedrive(img_bytes, filename, access_token)
                                
                                if upload_result["success"]:
                                    file_url = upload_result["url"]
                                else:
                                    # Fallback to local storage
                                    path = os.path.join(UPLOAD_FOLDER, filename)
                                    with open(path, 'wb') as f:
                                        f.write(img_bytes)
                                    file_url = filename
                            else:
                                # Fallback to local storage
                                path = os.path.join(UPLOAD_FOLDER, filename)
                                with open(path, 'wb') as f:
                                    f.write(img_bytes)
                                file_url = filename
                        else:
                            # For steps < 20,000 with screenshot, don't save the file
                            file_url = None
                    else:
                        # No screenshot provided (only allowed for steps < 20,000)
                        file_url = None
                    
                    # Insert into database
                    supabase.table("forms").insert({
                        "form_filepath": file_url,
                        "form_stepcount": steps,
                        "form_date": str(step_date),
                        "user_id": user_id,
                        "form_verified": False if steps >= 20000 else True  # Auto-verify if < 20k
                    }).execute()

                    # Record new submission time
                    st.session_state.last_submission_time = now

                    # Clear auto-fill value after successful submission
                    if "auto_fill_steps" in st.session_state:
                        del st.session_state.auto_fill_steps

                    st.success("✔ Step count submitted successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error("Error processing upload.")
                    st.exception(e)

# ------------------ TAB 2: AI Challenges ------------------
with tab2:
    st.header("✦ AI & Wellbeing Challenges")
    st.caption("Complete challenges and redeem your unique claim codes.")

    # ------------------ Mock Challenge Data (UI only) ------------------

    # ------------------ Challenges List ------------------
    from components import get_all_challenges
    Challenges = get_all_challenges()  # Load challenges to ensure file is read before code generation
    for ch in Challenges:
        with st.container(border=True):
            left, right = st.columns([8, 2])

            with left:
                st.subheader(Challenges[ch]["title"])
                st.write(Challenges[ch]["description"])
                st.caption(f"Reward: {Challenges[ch]['Reward']:,} steps")

            with right:
                # Check if user has already completed this challenge
                challenge_id = Challenges[ch]['id']
                expected_filepath = f"challenge_{challenge_id}_complete"
                toggle_key = f"show_redeem_{Challenges[ch]['id']}"
                challenge_completed = False
                
                try:
                    existing_completion = supabase.table("forms").select("*").eq("user_id", user_id).eq("form_filepath", expected_filepath).execute()
                    
                    if existing_completion.data:
                        st.success("Challenge Complete ✔")
                        challenge_completed = True
                    else:
                        if toggle_key not in st.session_state:
                            st.session_state[toggle_key] = False

                        if st.button("Redeem", key=f"redeem_btn_{Challenges[ch]['id']}", type="secondary"):
                            st.session_state[toggle_key] = not st.session_state[toggle_key]
                except Exception:
                    if toggle_key not in st.session_state:
                        st.session_state[toggle_key] = False

                    if st.button("Redeem", key=f"redeem_btn_{Challenges[ch]['id']}", type="secondary"):
                        st.session_state[toggle_key] = not st.session_state[toggle_key]

            # ------------------ Redeem UI ------------------
            if st.session_state.get(toggle_key, False) and not challenge_completed:
                st.markdown("**Redeem your challenge**")

                with st.form(key=f"redeem_form_{Challenges[ch]['id']}", clear_on_submit=True):
                    claim_code = st.text_input(
                        "Enter unique claim code",
                        placeholder="e.g. DXC-STEP-ABC123"
                    )

                    submitted = st.form_submit_button("Submit Code", type="primary")
                    from components import validate_claim_code
                    if submitted:
                        if not validate_claim_code(Challenges, claim_code, challenge_id):
                            st.error("Please enter a valid claim code.")
                        else:
                            try:
                                # Check if code has already been used by any user
                                code_hash = hashlib.sha256(claim_code.encode()).hexdigest()
                                existing_code_check = supabase.table("forms").select("*").eq("challenge_code", code_hash).execute()
                                
                                if existing_code_check.data:
                                    st.error("This code has already been used.")
                                else:
                                    # Insert challenge completion into forms table
                                    challenge_reward = Challenges[ch]['Reward']
                                    form_filepath = expected_filepath
                                    current_date = datetime.now().date()
                                    current_timestamp = datetime.now().isoformat()
                                    
                                    supabase.table("forms").insert({
                                        "form_filepath": form_filepath,
                                        "form_stepcount": challenge_reward,
                                        "form_date": str(current_date),
                                        "user_id": user_id,
                                        "form_created_at": current_timestamp,
                                        "form_verified": True,
                                        "challenge_code": code_hash
                                    }).execute()
                                    
                                    log_audit_event("CHALLENGE_REDEMPTION", user_email, f"Challenge ID: {challenge_id}, Code used")
                                    st.session_state[toggle_key] = False
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error processing challenge completion: {str(e)}")
                                logging.error(f"Challenge completion error: {e}")
# ------------------ TAB 3: DAILY PROGRESS ------------------
with tab3:
    st.header("➜ Daily Progress")
    st.caption("Track your step history, streaks, and statistics.")
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
        st.success(f"🗲 Current Streak: {streak} days" if streak else "No active streak.")

        # --- Graph ---
        fig = px.bar(
            daily_steps,
            x="form_date",
            y="form_stepcount",
            title=f"Steps per Day",
            color_discrete_sequence=["#7BA4DB"],
            labels={"form_date": "Date", "form_stepcount": "Step Count"},
            template="plotly_white"
        )
        fig.update_xaxes(tickformat="%Y-%m-%d")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Step Count",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, width='stretch')
        
        # ------------------ SUBMISSION HISTORY & DELETE ------------------
        st.markdown("---")
        st.subheader("Your Submission History")
        st.caption("View and manage your step submissions.")
        
        # Get all user submissions
        user_submissions = supabase.table("forms").select("*").eq("user_id", user_id).order("form_created_at", desc=True).execute()
        
        if user_submissions.data:
            # Prepare data for display
            submission_data = []
            for submission in user_submissions.data:
                submission_data.append({
                    "Date": submission['form_date'],
                    "Steps": submission['form_stepcount'],
                    "Submitted": submission['form_created_at'].split('T')[0] if 'T' in submission['form_created_at'] else submission['form_created_at'],
                    "Status": "Verified" if submission.get('form_verified') else "Pending",
                    "ID": submission['form_id']
                })
            
            # Display as table
            st.dataframe(
                pd.DataFrame(submission_data)[["Date", "Steps", "Submitted", "Status"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Delete submission section
            st.markdown("### Delete Submission")
            with st.expander("Delete a submission", expanded=False):
                st.warning("This action cannot be undone.")
                submission_ids = [s['form_id'] for s in user_submissions.data]
                submission_options = {f"{s['form_date']} - {s['form_stepcount']} steps": s['form_id'] for s in user_submissions.data}
                
                selected_submission = st.selectbox("Select submission to delete", list(submission_options.keys()))
                
                if st.button("Delete Selected Submission", type="secondary"):
                    submission_id = submission_options[selected_submission]
                    try:
                        supabase.table("forms").delete().eq("form_id", submission_id).eq("user_id", user_id).execute()
                        st.success("Submission deleted successfully.")
                        st.rerun()
                    except Exception:
                        st.error("Error deleting submission. Please try again.")
        else:
            st.info("No submissions found.")

# ------------------ TAB 4: TEAM MANAGEMENT ------------------
with tab4:
    st.header("⚑ Team Management")
    st.caption("Join or create teams to compete together.")
    
    # Get user's current team
    try:
        user_data = supabase.table("users").select("team_id").eq("user_id", user_id).execute()
        current_team_id = user_data.data[0].get("team_id") if user_data.data else None
    except Exception:
        current_team_id = None
    
    if current_team_id:
        # User is in a team - show team info
        try:
            team_info = supabase.table("teams").select("*").eq("team_id", current_team_id).execute()
            team_members = supabase.table("users").select("user_id, user_name").eq("team_id", current_team_id).execute()
            
            if team_info.data:
                team = team_info.data[0]
                
                st.subheader("Team Information")
                st.markdown(f"**Team Name:** {team['team_name']}")
                
                # Get team leader name from user_id
                try:
                    leader_info = supabase.table("users").select("user_name").eq("user_id", team['team_leader_id']).execute()
                    leader_name = leader_info.data[0]['user_name'] if leader_info.data else "Unknown"
                except Exception:
                    leader_name = "Unknown"
                st.markdown(f"**Team Leader:** {leader_name}")
                
                # Team member performance table
                st.subheader("Team Member Performance")
                
                # Get performance data for each team member
                member_data = []
                for member in team_members.data:
                    member_user_id = member['user_id']
                    member_name = member['user_name']
                    
                    # Get all forms for this member
                    try:
                        member_forms = supabase.table("forms").select("*").eq("user_id", member_user_id).execute()
                        
                        if member_forms.data:
                            total_steps = sum(f['form_stepcount'] for f in member_forms.data)
                            submission_count = len(member_forms.data)
                            
                            # Calculate average daily steps
                            if submission_count > 0:
                                avg_daily_steps = total_steps / submission_count
                            else:
                                avg_daily_steps = 0
                            
                            # Get last submission date
                            sorted_forms = sorted(member_forms.data, key=lambda x: x['form_created_at'], reverse=True)
                            last_submission = sorted_forms[0]['form_created_at'] if sorted_forms else "Never"
                            
                            # Calculate days since last submission
                            if last_submission != "Never":
                                try:
                                    last_date = datetime.fromisoformat(last_submission)
                                    days_since = (datetime.now() - last_date).days
                                    last_submission_display = f"{last_date.strftime('%Y-%m-%d')} ({days_since} days ago)"
                                except:
                                    last_submission_display = last_submission
                            else:
                                last_submission_display = "Never"
                        else:
                            total_steps = 0
                            avg_daily_steps = 0
                            last_submission_display = "Never"
                            submission_count = 0
                        
                        member_data.append({
                            "Team Member Name": member_name,
                            "Total Steps": total_steps,
                            "Average Daily Steps": round(avg_daily_steps),
                            "Total Submissions": submission_count,
                            "Last Submission": last_submission_display
                        })
                    except Exception:
                        member_data.append({
                            "Team Member Name": member_name,
                            "Total Steps": 0,
                            "Average Daily Steps": 0,
                            "Total Submissions": 0,
                            "Last Submission": "Error loading data"
                        })
                
                # Sort by total steps (descending)
                member_data.sort(key=lambda x: x["Total Steps"], reverse=True)
                
                # Display as non-interactive table
                if member_data:
                    st.dataframe(
                        pd.DataFrame(member_data),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No team member data available.")
                
                st.markdown("---")
                
                # Check if current user is the team leader
                is_team_leader = (user_id == team['team_leader_id'])
                
                if is_team_leader:
                    # Team leader can delete the team
                    if st.button("Delete Team", type="secondary", key="delete_team_btn"):
                        try:
                            # Unassign all team members
                            supabase.table("users").update({"team_id": None}).eq("team_id", current_team_id).execute()
                            # Delete the team
                            supabase.table("teams").delete().eq("team_id", current_team_id).execute()
                            st.success("Team deleted successfully. All members have been unassigned.")
                            st.rerun()
                        except Exception:
                            st.error("Error deleting team. Please try again.")
                else:
                    # Regular members can leave the team
                    if st.button("Leave Team", type="secondary", key="leave_team_btn"):
                        try:
                            supabase.table("users").update({"team_id": None}).eq("user_id", user_id).execute()
                            st.success("You have left the team.")
                            st.rerun()
                        except Exception:
                            st.error("Error leaving team. Please try again.")
        except Exception:
            st.error("Error loading team information. Please try again.")
    else:
        # User is not in a team
        # Check if user is already a team leader
        try:
            is_leader = supabase.table("teams").select("team_id").eq("team_leader_id", user_id).execute()
            user_is_leader = len(is_leader.data) > 0 if is_leader.data else False
        except Exception:
            user_is_leader = False
        
        # Show tabs based on whether user is a team leader
        if user_is_leader:
            # User is a team leader but not in a team - only show join option
            st.warning("You already created a team. You can only join existing teams.")
            
            st.subheader("Available Teams")
            try:
                all_teams = supabase.table("teams").select("*").execute()
                
                if all_teams.data:
                    available_teams = []
                    for team in all_teams.data:
                        members = supabase.table("users").select("user_id").eq("team_id", team["team_id"]).execute()
                        member_count = len(members.data) if members.data else 0
                        
                        if member_count < 4:
                            team["member_count"] = member_count
                            available_teams.append(team)
                    
                    if available_teams:
                        for team in available_teams:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"### {team['team_name']}")
                                # Get leader name
                                try:
                                    leader_info = supabase.table("users").select("user_name").eq("user_id", team['team_leader_id']).execute()
                                    leader_name = leader_info.data[0]['user_name'] if leader_info.data else "Unknown"
                                except Exception:
                                    leader_name = "Unknown"
                                st.caption(f"Leader: {leader_name}")
                            
                            with col2:
                                st.metric("Members", f"{team['member_count']}/4")
                            
                            with col3:
                                if st.button("Join", key=f"join_leader_{team['team_id']}", type="secondary"):
                                    try:
                                        supabase.table("users").update({"team_id": team['team_id']}).eq("user_id", user_id).execute()
                                        st.success("Successfully joined team!")
                                        st.rerun()
                                    except Exception:
                                        st.error("Error joining team.")
                            
                            st.markdown("---")
                    else:
                        st.info("No teams available to join.")
                else:
                    st.info("No teams exist yet.")
            except Exception:
                st.error("Error loading teams.")
        else:
            # User is not a team leader - show both tabs
            subtab1, subtab2 = st.tabs(["Join a Team", "Create a Team"])
            
            with subtab1:
                st.subheader("Available Teams")
                try:
                    all_teams = supabase.table("teams").select("*").execute()
                    
                    if all_teams.data:
                        available_teams = []
                        for team in all_teams.data:
                            members = supabase.table("users").select("user_id").eq("team_id", team["team_id"]).execute()
                            member_count = len(members.data) if members.data else 0
                            
                            if member_count < 4:
                                team["member_count"] = member_count
                                available_teams.append(team)
                        
                        if available_teams:
                            for team in available_teams:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                
                                with col1:
                                    st.markdown(f"### {team['team_name']}")
                                    # Get leader name
                                    try:
                                        leader_info = supabase.table("users").select("user_name").eq("user_id", team['team_leader_id']).execute()
                                        leader_name = leader_info.data[0]['user_name'] if leader_info.data else "Unknown"
                                    except Exception:
                                        leader_name = "Unknown"
                                    st.caption(f"Leader: {leader_name}")
                                
                                with col2:
                                    st.metric("Members", f"{team['member_count']}/4")
                                
                                with col3:
                                    if st.button("Join", key=f"join_{team['team_id']}", type="secondary"):
                                        try:
                                            supabase.table("users").update({"team_id": team['team_id']}).eq("user_id", user_id).execute()
                                            st.success("Successfully joined team!")
                                            st.rerun()
                                        except Exception:
                                            st.error("Error joining team.")
                                
                                st.markdown("---")
                        else:
                            st.info("No teams available to join.")
                    else:
                        st.info("No teams exist yet. Be the first to create one!")
                except Exception:
                    st.error("Error loading teams.")
            
            with subtab2:
                st.subheader("Create Your Team")
                st.write("As team leader, you'll manage your team.")
                
                with st.form("create_team_form"):
                    team_name = st.text_input(
                        "Team Name",
                        max_chars=50,
                        help="Choose a unique name for your team (3-50 characters)"
                    )
                    
                    submitted = st.form_submit_button("Create Team", type="secondary")
                    
                    if submitted:
                        if not team_name or len(team_name.strip()) < 3:
                            st.error("Team name must be at least 3 characters long.")
                        elif len(team_name.strip()) > 50:
                            st.error("Team name must be less than 50 characters.")
                        else:
                            try:
                                existing = supabase.table("teams").select("team_name").eq("team_name", team_name.strip()).execute()
                                
                                if existing.data:
                                    st.error("A team with this name already exists.")
                                else:
                                    team_response = supabase.table("teams").insert({
                                        "team_name": team_name.strip(),
                                        "team_leader_id": user_id
                                    }).execute()
                                    
                                    if team_response.data:
                                        new_team_id = team_response.data[0]["team_id"]
                                        supabase.table("users").update({"team_id": new_team_id}).eq("user_id", user_id).execute()
                                        
                                        st.success(f"Team '{team_name}' created successfully!")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error("Error creating team.")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

# ------------------ FOOTER (ALWAYS RENDER) ------------------
render_footer()