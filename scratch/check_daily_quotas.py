import os, json, urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY", "").strip("\"'")

test_models = [
    "allam-2-7b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]

for m in test_models:
    body = {"model": m, "messages": [{"role": "user", "content": "SELECT 1;"}], "max_tokens": 10}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            hdrs = dict(resp.info())
            tpd_rem = hdrs.get("x-ratelimit-remaining-tokens", "N/A")
            tpd_lim = hdrs.get("x-ratelimit-limit-tokens", "N/A")
            rpd_rem = hdrs.get("x-ratelimit-remaining-requests", "N/A")
            print(f"{m}: OK! Tokens rem: {tpd_rem}/{tpd_lim}, Requests rem: {rpd_rem}")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"{m}: HTTP {e.code}: {err[:140]}")
    except Exception as e:
        print(f"{m}: Error: {e}")
