import os, json, urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY", "").strip("\"'")
req = urllib.request.Request("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}", "User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        for m in sorted([x["id"] for x in data.get("data", [])]):
            print(m)
except Exception as e:
    print("Error:", e)
