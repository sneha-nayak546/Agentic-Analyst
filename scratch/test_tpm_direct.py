import os, json, urllib.request
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GROQ_API_KEY", "").strip("\"'")

for m in ["qwen/qwen3.6-27b", "openai/gpt-oss-20b"]:
    body = {"model": m, "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            hdrs = dict(resp.info())
            print(f"{m}: limit={hdrs.get('x-ratelimit-limit-tokens')}, rem={hdrs.get('x-ratelimit-remaining-tokens')}")
    except Exception as e:
        print(f"{m} err: {e}")
