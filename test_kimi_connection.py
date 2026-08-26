import os
import time
import json
import requests
from dotenv import load_dotenv

# Fix Windows console encoding for emojis
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

def run_connectivity_test():
    print("=" * 60)
    print(" 🚀 JGH Intelligence Engine — Kimi Connectivity Test")
    print("=" * 60)

    # 1. Load KIMI_API_KEY from .env
    load_dotenv()
    api_key = os.getenv("KIMI_API_KEY")
    base_url = "https://api.moonshot.cn/v1/chat/completions"
    model = os.getenv("LLM_MODEL", "moonshot-v1-8k")

    if not api_key:
        print("❌ Error: KIMI_API_KEY not found in .env")
        return False

    print(f"[*] Configuration Loaded")
    print(f"[*] Model: {model}")
    print(f"[*] Base URL: {base_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Test 1: Basic text completion
    print("\n[Test 1] Basic Text Completion (KIMI_CONNECTION_OK)")
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Reply with exactly: KIMI_CONNECTION_OK"}
        ],
        "temperature": 0.0,
        "max_tokens": 50
    }

    t0 = time.time()
    try:
        res = requests.post(base_url, headers=headers, json=payload, timeout=10)
        latency = round((time.time() - t0) * 1000, 2)
        
        print(f"  HTTP Status: {res.status_code}")
        print(f"  Response Time: {latency} ms")
        
        if res.status_code == 401:
            print("  ❌ Authentication Failed (HTTP 401 Unauthorized).")
            print("  Please check your KIMI_API_KEY in .env.")
            return False
        elif res.status_code != 200:
            print(f"  ❌ API Error: {res.text[:200]}")
            return False
            
        data = res.json()
        content = data['choices'][0]['message']['content'].strip()
        print(f"  Response: {content}")
        
        if "KIMI_CONNECTION_OK" in content:
            print("  ✅ Test 1 Passed.")
        else:
            print("  ⚠️ Test 1 Failed. Unexpected response.")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection Error: {str(e)}")
        return False

    # Test 2: Structured JSON
    print("\n[Test 2] Structured JSON Parsing")
    payload2 = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Return a JSON object with two keys: 'status' set to 'success', and 'confidence' set to 99. Do not include markdown."}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    t0 = time.time()
    try:
        res2 = requests.post(base_url, headers=headers, json=payload2, timeout=10)
        latency2 = round((time.time() - t0) * 1000, 2)
        
        print(f"  HTTP Status: {res2.status_code}")
        print(f"  Response Time: {latency2} ms")
        
        if res2.status_code == 200:
            data2 = res2.json()
            content2 = data2['choices'][0]['message']['content'].strip()
            print(f"  Raw Content: {content2}")
            
            try:
                parsed = json.loads(content2)
                if parsed.get("status") == "success" and parsed.get("confidence") == 99:
                    print("  ✅ Test 2 Passed (JSON verified).")
                else:
                    print("  ⚠️ Test 2 Failed. JSON format unexpected.")
                    return False
            except json.JSONDecodeError:
                print("  ❌ Test 2 Failed. LLM did not return valid JSON.")
                return False
        else:
            print(f"  ❌ Test 2 Failed. HTTP {res2.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Connection Error: {str(e)}")
        return False
        
    print("\n============================================================")
    print(" ✅ ALL KIMI CONNECTIVITY TESTS PASSED")
    print("============================================================")
    return True

if __name__ == "__main__":
    run_connectivity_test()
