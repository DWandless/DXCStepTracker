# db.py
from supabase import create_client, ClientOptions
import streamlit as st

# Load credentials from Streamlit secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

if not url or not key:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set in environment")

# Client options for Supabase v2.24.0
options = ClientOptions(
    auto_refresh_token=True,
    persist_session=False,
)

supabase = create_client(url, key, options)
