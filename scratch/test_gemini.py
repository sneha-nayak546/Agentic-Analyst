import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
model = "gemini-2.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

body = {
    "contents": [{"parts": [{"text": "Hello, respond with: {\"status\": \"ok\"}"}]}],
    "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
}

req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("Success! Candidate text:")
        print(res["candidates"][0]["content"]["parts"][0]["text"])
except Exception as e:
    print("Error:", e)
