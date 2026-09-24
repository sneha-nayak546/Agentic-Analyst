import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY", "").strip("\"'")

req = urllib.request.Request(
    "https://api.groq.com/openai/v1/models",
    headers={
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = [m["id"] for m in data.get("data", [])]
        print("Available Groq Models:")
        for m in sorted(models):
            print(" -", m)
except Exception as e:
    print("Error querying Groq models:", e)
