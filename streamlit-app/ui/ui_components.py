"""
Reusable UI components for DXC Step Tracker.
Handles header, footer, sidebar, and common UI patterns.
"""

import streamlit as st
import html
from datetime import datetime
from pathlib import Path
from .theme import LOGO_PATH


def setup_logo():
    """Setup the logo in the sidebar."""
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), icon_image=str(LOGO_PATH), size="large")
    else:
        st.warning(f"Logo not found at: {LOGO_PATH}")


def render_header(title: str, subtitle: str):
    """
    Render the DXC Technology header with blue gradient background.
    
    Args:
        title: Main header title
        subtitle: Subtitle text
    """
    # Escape user-generated content to prevent XSS
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    
    st.markdown(
        f"""
        <div class="header-container">
            <div>
                <div class="header-title">{safe_title}</div>
                <div class="header-subtitle">{safe_subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_footer():
    """Render the DXC Technology footer with blue divider."""
    st.markdown(
        "<div style='margin-top:60px; padding-top:20px; border-top:3px solid #7BA4DB;'></div>",
        unsafe_allow_html=True
    )


def render_sidebar_welcome(display_name=None):
    """
    Render welcome message in sidebar with logout button.
    Uses display_name from session state if not provided.
    
    Args:
        display_name: Display name to show (optional, defaults to session state)
        
    Returns:
        bool: True if logout button was clicked
    """
    if display_name is None:
        display_name = st.session_state.get("display_name", st.session_state.get("username", "User"))
    
    # Escape user-generated content to prevent XSS
    safe_display_name = html.escape(display_name)
    
    st.sidebar.markdown(
        f"<h3 style='color:#7BA4DB;'>Welcome, {safe_display_name}!</h3>",
        unsafe_allow_html=True
    )
    return st.sidebar.button("Logout", type="secondary")


def handle_logout():
    """Handle logout by clearing session state."""
    st.session_state.clear()
    st.rerun()


def check_login_required():
    """
    Check if user is logged in. If not, show warning and stop execution.
    
    Returns:
        str: Username if logged in, otherwise stops execution
    """
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()
    
    # Check session timeout (8 hours)
    login_time = st.session_state.get("login_time")
    if login_time:
        session_timeout = 8 * 3600  # 8 hours in seconds
        if datetime.now().timestamp() - login_time > session_timeout:
            st.warning("Session expired. Please log in again.")
            handle_logout()
    
    return st.session_state.get("username")
