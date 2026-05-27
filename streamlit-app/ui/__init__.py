"""UI components and theming modules."""

import streamlit as st
import base64
import html
from datetime import datetime
from pathlib import Path

# Paths + Static Assets
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / ".streamlit" / "static" / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
HEADER_FONT_PATH = ASSETS_DIR / "GT-Standard-L-Extended-Medium.otf"


def apply_header_font():
    """Apply the GT-Standard font to headers using base64 encoding."""
    if not HEADER_FONT_PATH.exists():
        return
    try:
        font_b64 = base64.b64encode(HEADER_FONT_PATH.read_bytes()).decode("utf-8")
    except Exception:
        return
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'GTStandardHeader';
            src: url(data:font/otf;base64,{font_b64}) format('opentype');
            font-weight: 500;
            font-style: normal;
        }}
        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6,
        .header-title, .header-subtitle {{
            font-family: 'GTStandardHeader', sans-serif !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_dxc_theme():
    """Apply the DXC gradient theme and styling to the page."""
    apply_header_font()
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, 
                #FFFFFF 0%, #F8FBFF 25%, #E3F2FD 50%, #FFF3E0 75%, #FFE0B2 100%
            );
            min-height: 100vh;
        }
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
        .stButton>button:not([kind="secondary"]) {
            background: linear-gradient(90deg, #7BA4DB, #FF9A6C);
            color: white;
            border-radius: 8px;
            font-weight: bold;
            transition: 0.3s;
            border: none;
        }
        .stButton>button:not([kind="secondary"]):hover {
            background: linear-gradient(90deg, #6B94CB, #EF8A5C);
            transform: scale(1.05);
        }
        .stButton>button[kind="secondary"],
        .stFormSubmitButton>button {
            background-color: #FFFFFF !important;
            border: 1px solid #7BA4DB !important;
            color: #31333F !important;
            border-radius: 8px;
            font-weight: bold;
        }
        .stButton>button[kind="secondary"]:hover,
        .stFormSubmitButton>button:hover {
            background-color: #F8FBFF !important;
            border: 1px solid #6B94CB !important;
        }
        [data-testid="stSidebar"] {
            border-right: 2px solid #7BA4DB !important;
        }
    </style>
    """, unsafe_allow_html=True)


def hide_streamlit_branding():
    """Hide Streamlit's default branding elements."""
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


def setup_logo():
    """Setup the logo in the sidebar."""
    if LOGO_PATH.exists():
        st.logo(str(LOGO_PATH), icon_image=str(LOGO_PATH), size="large")
    else:
        st.warning(f"Logo not found at: {LOGO_PATH}")


def render_header(title: str, subtitle: str):
    """Render the DXC Technology header with blue gradient background."""
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
    """Render welcome message in sidebar with logout button."""
    if display_name is None:
        display_name = st.session_state.get("display_name", st.session_state.get("username", "User"))
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
    """Check if user is logged in. If not, show warning and stop execution."""
    if not st.session_state.get("logged_in"):
        st.warning("Please log in first.")
        st.stop()
    login_time = st.session_state.get("login_time")
    if login_time:
        session_timeout = 8 * 3600
        if datetime.now().timestamp() - login_time > session_timeout:
            st.warning("Session expired. Please log in again.")
            handle_logout()
            st.stop()
    return st.session_state.get("username")


# Import excel_export function
from .excel_export import generate_comprehensive_export

__all__ = [
    'apply_dxc_theme',
    'hide_streamlit_branding',
    'apply_header_font',
    'setup_logo',
    'render_header',
    'render_footer',
    'render_sidebar_welcome',
    'handle_logout',
    'check_login_required',
    'generate_comprehensive_export'
]
