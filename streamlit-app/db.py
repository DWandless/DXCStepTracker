"""
# db.py
from supabase import create_client
from supabase.lib.client_options import ClientOptions
import httpx
import streamlit as st

# Load environment variables from streamlit secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

if not url or not key:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set in environment")

options = ClientOptions(httpx_client=httpx.Client(verify=True))

supabase = create_client(url, key, options=options)

"""


# db.py
from supabase import create_client, ClientOptions
import streamlit as st

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

if not url or not key:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set in environment")

# Use the modern ClientOptions class (with expected fields)
options = ClientOptions(
    auto_refresh_token=True,
    persist_session=False,
    detect_session_in_url=False,
)

supabase = create_client(url, key, options)