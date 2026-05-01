import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "mutual_fund_faqs")

print(f"Connecting to {CHROMA_HOST}...")
client = chromadb.CloudClient(
    tenant=CHROMA_TENANT,
    database=CHROMA_DATABASE,
    api_key=CHROMA_API_KEY
)

try:
    collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
    print(f"Collection '{CHROMA_COLLECTION_NAME}' found.")
    print(f"Count: {collection.count()}")
    peek = collection.peek(limit=1)
    print(f"Peek: {peek}")
except Exception as e:
    print(f"Error: {e}")
