import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

test_models = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest"
]

for model in test_models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"parts": [{"text": "Say OK"}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 10}
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"[SUCCESS] {model}: {text}")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"[HTTP {e.code}] {model}: {err[:120]}")
    except Exception as e:
        print(f"[FAIL] {model}: {e}")
