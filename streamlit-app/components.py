"""
Shared components and styling for the DXC Step Tracker application.
This module contains reusable functions for consistent theming across all pages.
"""
import streamlit as st
from pathlib import Path
from streamlit.components.v1 import html as st_html


def apply_dxc_theme():
    """Apply the DXC gradient theme and styling to the page."""
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
        .header-title { font-size: 42px; font-weight: bold; }
        .header-subtitle { font-size: 18px; margin-top: 5px; }
        
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


def setup_logo(base_path=None):
    """
    Set up the DXC logo in the sidebar.
    
    Args:
        base_path: Path object pointing to the directory containing assets folder.
                  If None, assumes current file's parent directory.
    """
    if base_path is None:
        base_path = Path(__file__).parent
    
    logo_path = base_path / "assets" / "logo.png"
    
    if logo_path.exists():
        st.logo(str(logo_path), icon_image=str(logo_path), size="large")
    else:
        st.warning(f"⚠️ Logo not found at: {logo_path}")


def render_header(title, subtitle):
    """
    Render a styled header with title and subtitle.
    
    Args:
        title: Main header title
        subtitle: Subtitle text
    """
    st.markdown(f"""
    <div class="header-container">
        <div>
            <div class="header-title">{title}</div>
            <div class="header-subtitle">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the DXC Technology footer."""
    st.markdown(
        "<div class='footer-branding' style='text-align:center; font-weight:bold; margin-top:40px; padding-top:20px; border-top:2px solid #7BA4DB;'>DXC Technology</div>",
        unsafe_allow_html=True
    )


def render_sidebar_welcome(username):
    """
    Render welcome message in sidebar with logout button.
    
    Args:
        username: Username to display
        
    Returns:
        bool: True if logout button was clicked
    """
    st.sidebar.markdown(
        f"<h3 style='color:#7BA4DB;'>Welcome, {username}!</h3>",
        unsafe_allow_html=True
    )
    return st.sidebar.button("Logout")


def hide_streamlit_branding():
    """Hide Streamlit's default branding elements."""
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


def check_login_required():
    """
    Check if user is logged in. If not, show warning and stop execution.
    
    Returns:
        str: Username if logged in, otherwise stops execution
    """
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()
    
    return st.session_state.get("username", "Guest")


def handle_logout():
    """Handle user logout by clearing session state and rerunning."""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()
