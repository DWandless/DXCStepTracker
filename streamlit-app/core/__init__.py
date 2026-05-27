"""Core authentication and database modules."""

# Import auth functions
from .auth import initialize_session_state, handle_oauth_redirect, process_login, get_login_url, require_admin, is_admin

# Import supabase with fallback
try:
    from .db import supabase
except ImportError:
    from core.db import supabase

__all__ = [
    'initialize_session_state',
    'handle_oauth_redirect',
    'process_login',
    'get_login_url',
    'require_admin',
    'is_admin',
    'supabase'
]
