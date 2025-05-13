import os

from dotenv import load_dotenv
from supabase import create_client, Client

from src.database.FakeSupabaseClient import FakeSupabaseClient
from src.utils import printc

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client
if not SUPABASE_URL or not SUPABASE_KEY:
    printc("[WARN] Supabase URL or key not found in .env file. Database connection has not been established!", color="orange")
    # Use a fake client class, so errors aren't thrown when calling supabase's methods
    supabase = FakeSupabaseClient()  # type: ignore
else:
    # Initialize real Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
