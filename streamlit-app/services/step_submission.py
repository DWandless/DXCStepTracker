"""
Step submission business logic module for DXC Step Tracker.
Handles step validation, submission limits, and file processing.
"""

import os
import io
import logging
from datetime import datetime, timedelta
from PIL import Image, UnidentifiedImageError
from core.db import supabase
from utils.onedrive_storage import upload_to_onedrive, get_access_token


def validate_step_submission(steps, screenshot, max_size=5 * 1024 * 1024):
    """
    Validate a step submission before processing.
    
    Args:
        steps: Step count to validate
        screenshot: Uploaded screenshot file
        max_size: Maximum file size in bytes (default 5MB)
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if steps <= 0 or steps > 100000:
        return False, "Enter a valid step count (1–100,000)."
    
    if steps >= 20000 and not screenshot:
        return False, "Screenshot required for submissions 20,000+ steps."
    
    if screenshot and screenshot.size > max_size:
        return False, "File too large. Max 5 MB."
    
    if screenshot:
        try:
            Image.open(screenshot)
        except UnidentifiedImageError:
            return False, "Invalid image."
    
    return True, None


def check_submission_cooldown(user_id, cooldown_seconds=30):
    """
    Check if user is within submission cooldown period.
    
    Args:
        user_id: User ID to check
        cooldown_seconds: Cooldown period in seconds (default 30)
        
    Returns:
        tuple: (can_submit, remaining_seconds)
    """
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
            last_submission_time = datetime.fromisoformat(response.data[0]["form_created_at"])
            time_since_last = datetime.now() - last_submission_time
            
            if time_since_last < timedelta(seconds=cooldown_seconds):
                remaining = timedelta(seconds=cooldown_seconds) - time_since_last
                return False, int(remaining.total_seconds())
    except Exception as e:
        logging.error(f"Error checking submission cooldown: {e}")
    
    return True, 0


def check_daily_submission_limit(user_id, max_daily=10):
    """
    Check if user has exceeded daily submission limit.
    
    Args:
        user_id: User ID to check
        max_daily: Maximum submissions per day (default 10)
        
    Returns:
        tuple: (within_limit, current_count)
    """
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_submissions = supabase.table("forms") \
            .select("form_id") \
            .eq("user_id", user_id) \
            .gte("form_created_at", today_start.isoformat()) \
            .execute()
        
        submission_count = len(daily_submissions.data) if daily_submissions.data else 0
        return submission_count < max_daily, submission_count
    except Exception as e:
        logging.error(f"Error checking daily submission limit: {e}")
        return True, 0  # Allow submission if check fails


def process_screenshot_upload(screenshot, safe_username, step_date, steps, upload_folder):
    """
    Process and upload screenshot to OneDrive or local storage.
    
    Args:
        screenshot: Uploaded screenshot file
        safe_username: Safe username for filename
        step_date: Date of the step submission
        steps: Step count (determines if OneDrive upload is required)
        upload_folder: Local upload folder path
        
    Returns:
        tuple: (file_url, error_message)
    """
    try:
        img = Image.open(screenshot).convert("RGB")
        filename = f"{safe_username}_{step_date}_{datetime.now().strftime('%H%M%S')}.jpg"
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG", quality=85, optimize=True)
        img_bytes = img_byte_arr.getvalue()
        
        file_url = None
        
        # For steps >= 20,000, upload to OneDrive
        if steps >= 20000:
            access_token = get_access_token()
            
            if access_token:
                upload_result = upload_to_onedrive(img_bytes, filename, access_token)
                
                if upload_result["success"]:
                    file_url = upload_result["url"]
                else:
                    # Fallback to local storage
                    path = os.path.join(upload_folder, filename)
                    with open(path, 'wb') as f:
                        f.write(img_bytes)
                    file_url = filename
            else:
                # Fallback to local storage
                path = os.path.join(upload_folder, filename)
                with open(path, 'wb') as f:
                    f.write(img_bytes)
                file_url = filename
        else:
            # For steps < 20,000 with screenshot, don't save the file
            file_url = None
        
        return file_url, None
    except Exception as e:
        logging.error(f"Error processing screenshot: {e}")
        return None, str(e)


def submit_step_form(user_id, steps, step_date, file_url, verified=False):
    """
    Submit a step form to the database.
    
    Args:
        user_id: User ID submitting the form
        steps: Step count
        step_date: Date of the steps
        file_url: URL to screenshot file (if any)
        verified: Whether the submission is auto-verified
        
    Returns:
        tuple: (success, error_message)
    """
    try:
        supabase.table("forms").insert({
            "form_filepath": file_url,
            "form_stepcount": steps,
            "form_date": str(step_date),
            "user_id": user_id,
            "form_verified": verified
        }).execute()
        return True, None
    except Exception as e:
        logging.error(f"Error submitting step form: {e}")
        return False, str(e)


def get_last_submission_time(user_id):
    """
    Get the last submission time for a user.
    
    Args:
        user_id: User ID to check
        
    Returns:
        datetime of last submission, or None if no submissions
    """
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
