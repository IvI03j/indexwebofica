from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

supabase = None

if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
