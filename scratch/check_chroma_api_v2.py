import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("CHROMA_API_KEY")
tenant = os.getenv("CHROMA_TENANT")
database = os.getenv("CHROMA_DATABASE")

print(f"Testing CloudClient with tenant={tenant}, database={database}...")
try:
    client = chromadb.CloudClient(
        tenant=tenant,
        database=database,
        api_key=api_key
    )
    print("Heartbeat:", client.heartbeat())
    print("Collections:", client.list_collections())
except Exception as e:
    print(f"Error: {e}")
