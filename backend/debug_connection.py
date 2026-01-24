from app.core.supabase import supabase
import os

print("--- DEBUGGING SUPABASE ---")

# 1. Check Variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url:
    print("ERROR: SUPABASE_URL is Missing from environment!")
if not key:
    print("ERROR: SUPABASE_KEY is Missing from environment!")

if url and key:
    print("Environment Variables: OK")
    print(f"URL: {url[:10]}...") # Print first 10 chars only for safety

# 2. Check Connection
try:
    print("Attempting to fetch students...")
    # Try lowercase 'student' first as Postgres defaults to lowercase
    response = supabase.table("student").select("*").execute()
    print("Connection Successful!")
    print(f"Found {len(response.data)} students.")
except Exception as e:
    print("\nCRITICAL ERROR:")
    print(e)
