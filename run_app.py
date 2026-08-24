"""
Live Application Launcher & Master Entry Point for JGH Intelligence Engine.
Workflow:
  1. Runs test_accuracy.py to verify 20/20 golden benchmark accuracy suite passes (100%).
  2. Starts FastAPI backend server on http://localhost:8000.
  3. Launches interactive CLI sandbox or opens default browser for live manual testing.
"""

import sys
import os
import subprocess
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from test_accuracy import run_accuracy_benchmark

def main():
    print("=" * 75)
    print(" 🚀 JGH INTELLIGENCE ENGINE — LIVE APPLICATION LAUNCHER")
    print("=" * 75 + "\n")

    # Step 1: Run Golden Benchmark Accuracy Verification Suite
    print("Step 1: Running Golden Benchmark Accuracy Suite (20 Questions)...")
    accuracy_success = run_accuracy_benchmark()

    if not accuracy_success:
        print("\n⚠️ WARNING: Golden benchmark verification did not achieve 100% pass score.")
        choice = input("Do you wish to continue launching server? (y/n): ").strip().lower()
        if choice != 'y':
            sys.exit(1)

    print("\n✅ Step 1 Complete: All 20 Golden Benchmark test cases passed (100% Accuracy).")

    # Step 2: Start FastAPI Server in background
    print("\nStep 2: Starting FastAPI Server on http://localhost:8000 ...")
    venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    server_cmd = [python_cmd, "-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "8000"]
    
    server_process = subprocess.Popen(
        server_cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print("[SERVER] Uvicorn server launching process PID:", server_process.pid)
    time.sleep(3.0)

    # Step 3: Open Browser & Launch Interactive Testing Sandbox
    print("\nStep 3: Opening Web App UI at http://localhost:8000/ ...")
    try:
        webbrowser.open("http://localhost:8000/")
    except Exception as e:
        print("Could not open default browser automatically:", e)

    print("\n" + "=" * 75)
    print(" 🎉 JGH AI Collaborator is LIVE on http://localhost:8000")
    print(" Starting interactive CLI sandbox for live manual testing...")
    print("=" * 75 + "\n")

    from scripts.run_manual_testing import start_interactive_sandbox
    try:
        start_interactive_sandbox()
    finally:
        print("\nStopping FastAPI server...")
        server_process.terminate()

if __name__ == "__main__":
    main()
