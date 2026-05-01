import requests
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("CHROMA_HOST", "api.trychroma.com")
port = os.getenv("CHROMA_PORT", "443")
api_key = os.getenv("CHROMA_API_KEY")
tenant = os.getenv("CHROMA_TENANT", "default_tenant")
database = os.getenv("CHROMA_DATABASE", "default_database")

heartbeat_url = f"https://{host}:{port}/api/v1/heartbeat"
collections_url = f"https://{host}:{port}/api/v1/collections?tenant={tenant}&database={database}"

headers = {}
if api_key:
    headers["Authorization"] = f"Bearer {api_key}"

def test_url(name, url):
    print(f"Testing {name}: {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

test_url("Heartbeat", heartbeat_url)
test_url("Collections", collections_url)
