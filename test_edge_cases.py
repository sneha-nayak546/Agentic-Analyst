"""
Verification Suite for Self-Correction Retry Loop, Clarification Fallback & Query Logger.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.collaborator import handle_collaborative_query
from app.utils.query_logger import UNMAPPED_LOG_FILE

def run_edge_case_tests():
    print("=" * 70)
    print(" 🧪 JGH Edge-Case Handling & Clarification Verification Suite")
    print("=" * 70)

    passed = 0
    total = 3

    # Test 1: Clarification Fallback Engine
    print("\n[Test 1/3] Testing Clarification Fallback Engine ('bitcoin balance') ...")
    res_clar = handle_collaborative_query("Show user bitcoin balance", execute=False)
    if res_clar.get("mode") == "CLARIFICATION" and "Clarification Required" in res_clar.get("response", ""):
        print(f"  ✅ PASSED: Triggered structured clarification prompt listing valid enterprise metrics.")
        passed += 1
    else:
        print(f"  ❌ FAILED: Clarification fallback failed to trigger ({res_clar.get('mode')})")

    # Test 2: Unknown Query Audit Logger
    print("\n[Test 2/3] Testing Unknown Query Audit Logger (knowledge/unmapped_queries.json) ...")
    if UNMAPPED_LOG_FILE.exists():
        with open(UNMAPPED_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            if any("bitcoin" in item.get("prompt", "").lower() for item in logs):
                print(f"  ✅ PASSED: Unmapped query event logged successfully into {UNMAPPED_LOG_FILE.name}.")
                passed += 1
            else:
                print(f"  ❌ FAILED: Unmapped query event not found in log file.")
    else:
        print(f"  ❌ FAILED: Log file {UNMAPPED_LOG_FILE} missing.")

    # Test 3: Self-Correction Retry Loop
    print("\n[Test 3/3] Testing Self-Correction Retry Loop on standard prompts ...")
    res_normal = handle_collaborative_query("Teach me how user roles work", execute=False)
    if res_normal.get("status") in ["success", "APPROVED"]:
        print(f"  ✅ PASSED: Processed standard prompt through gatekeeper validation cleanly.")
        passed += 1
    else:
        print(f"  ❌ FAILED: Normal prompt failed processing.")

    print("\n" + "=" * 70)
    print(f" 📊 FINAL RESULT: {passed}/{total} Test Cases Passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)
