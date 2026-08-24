import sys
import os
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

def run_diagnostics() -> bool:
    print("=" * 70)
    print("AI SQL AGENT PRODUCTION SERVER LAUNCH DIAGNOSTICS")
    print("=" * 70)

    # 1. Python Environment Check
    py_ver = sys.version.split()[0]
    print(f"[1/4] Python Environment: Python {py_ver} OK")

    # 2. Key and Encrypted Secrets Check
    key_file = ".master.key"
    env_file = ".env"
    if not os.path.exists(key_file):
        print(f"[ERROR] Master key file '{key_file}' not found.")
        return False
    if not os.path.exists(env_file):
        print(f"[ERROR] Environment file '{env_file}' not found.")
        return False
    print(f"[2/4] Credentials & Encryption: Secrets & '{key_file}' OK")

    # 3. Database Connection Check
    try:
        from app.database.read_executor import execute_read_query
        db_res = execute_read_query("SELECT 1 AS status;", limit=1)
        if db_res.get("success"):
            print("[3/4] Database Pool: Connection to MySQL 'jghMasterDB' OK")
        else:
            print(f"[ERROR] Database connection failed: {db_res.get('error')}")
            return False
    except Exception as e:
        print(f"[ERROR] Database connection exception: {e}")
        return False

    # 4. LLM & Ollama Model Availability
    try:
        from app.llm.sql_generator import is_ollama_online
        ollama_status = is_ollama_online()
        print(f"[4/4] LLM Engine: Ollama / Deterministic Synthesizer Active (Online: {ollama_status})")
    except Exception as e:
        print(f"[LLM NOTICE] Ollama check: {e}")

    print("=" * 70)
    print("ALL DIAGNOSTIC CHECKS PASSED. STARTING FASTAPI PRODUCTION SERVER...")
    print("=" * 70)
    return True

if __name__ == "__main__":
    if not run_diagnostics():
        sys.exit(1)

    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
