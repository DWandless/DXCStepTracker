# db.py
import os
from dotenv import load_dotenv
from supabase import create_client
from supabase.lib.client_options import ClientOptions
import httpx

# Load env and create the client once
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set in environment")

# TODO: Remove verify=False in production, therefore make True for deployment
options = ClientOptions(httpx_client=httpx.Client(verify=False))

supabase = create_client(url, key, options=options)
