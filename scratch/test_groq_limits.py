import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY", "").strip("\"'")

test_models = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b", "groq/compound-mini"]

for m in test_models:
    body = {
        "model": m,
        "messages": [{"role": "user", "content": "SELECT 1;"}],
        "max_tokens": 10
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            hdrs = dict(resp.info())
            tpm_rem = hdrs.get("x-ratelimit-remaining-tokens", "N/A")
            tpm_lim = hdrs.get("x-ratelimit-limit-tokens", "N/A")
            rpd_rem = hdrs.get("x-ratelimit-remaining-requests", "N/A")
            rpd_lim = hdrs.get("x-ratelimit-limit-requests", "N/A")
            print(f"Model: {m}")
            print(f"  Tokens: limit={tpm_lim}, remaining={tpm_rem}")
            print(f"  Requests: limit={rpd_lim}, remaining={rpd_rem}")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Model: {m} -> HTTP {e.code}: {err[:120]}")
    except Exception as e:
        print(f"Model: {m} -> Error: {e}")
