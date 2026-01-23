import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("https://xjcpgggxrajdjdmtdqcl.supabase.co")
key: str = os.environ.get("sb_secret_ySGYvihLGkfpYCqpAoHYOg_ARD3w-_u")

supabase: Client = create_client(url, key)