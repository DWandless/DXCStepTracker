"""
Core utility functions for DXC Step Tracker.
This module contains shared utility functions used across the application.
"""

import streamlit as st
import logging
import os
import re
import unicodedata
import json
from pathlib import Path


# ==================== UTILITY FUNCTIONS ====================

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        filename="app.log",
        level=logging.ERROR,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def log_audit_event(event_type, user_email, details=None):
    """
    Log audit events for sensitive operations.
    
    Args:
        event_type: Type of event (e.g., "VERIFICATION", "CODE_GENERATION", "ADMIN_ACCESS")
        user_email: Email of the user performing the action
        details: Additional details about the event (optional)
    """
    try:
        # Sanitize email for logging
        safe_email = user_email[:3] + "***@***" if user_email else "unknown"
        
        log_message = f"AUDIT: {event_type} - User: {safe_email}"
        if details:
            log_message += f" - Details: {details}"
        
        logging.info(log_message)
    except Exception as e:
        logging.error(f"Failed to log audit event: {e}")


def secure_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filenames to prevent directory traversal or injection.
    
    Args:
        filename: Original filename
        max_length: Maximum allowed length
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "file"
    filename = os.path.basename(filename)
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^A-Za-z0-9.\-_]", "_", filename)
    return filename[:max_length]


def get_met_values():
    """
    Fetch MET values from the MetValues.json file.
    
    Returns:
        Dict of activity names to MET step values, or empty dict if file not found or invalid
    """
    try:
        base_dir = Path(__file__).resolve().parent.parent
        met_path = base_dir / ".streamlit" / "static" / "assets" / "MetValues.json"
        
        if not met_path.exists():
            met_path = base_dir / "static" / "assets" / "MetValues.json"
        if not met_path.exists():
            met_path = base_dir / "assets" / "MetValues.json"
        
        if not met_path.exists():
            error_msg = f"MetValues.json not found at: {met_path}"
            logging.error(error_msg)
            return {}
        
        with open(met_path, "r") as f:
            met_values = json.load(f)
            return met_values
    except Exception as e:
        error_msg = f"Error loading MET values: {e}"
        logging.error(error_msg)
        return {}


# ==================== BACKWARD COMPATIBILITY IMPORTS ====================
# Re-export functions from new modules for backward compatibility
from ui.theme import apply_dxc_theme, hide_streamlit_branding
from ui.ui_components import render_header, render_footer, render_sidebar_welcome, setup_logo, handle_logout, check_login_required
from services.data_services import get_user_id, fetch_user_forms
from core.auth import is_admin
from services.challenges import get_all_challenges, generate_claim_code, hash_claim_code, validate_claim_code
