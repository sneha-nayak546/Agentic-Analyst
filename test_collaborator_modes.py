"""
Verification Suite for JGH Full-Spectrum AI Collaborator Modes.
Tests all 5 operational intent modes:
  1. TUTOR_QA        - Database Tutor & Onboarding Coach
  2. ERD_GEN         - ERD & Visual Architecture Generator
  3. DASHBOARD_GEN   - Dynamic Dashboard Spec Builder
  4. BUSINESS_STORY  - Executive Business Storyteller
  5. SQL_ANALYTICS   - Tested v2.0 Text-to-SQL Execution Pipeline
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.intent_router import route_intent
from app.agent.collaborator import handle_collaborative_query

def run_collaborator_tests():
    print("=" * 70)
    print(" 🧪 JGH AI Collaborator — 5 Operational Modes Verification Suite")
    print("=" * 70)

    test_cases = [
        {
            "id": 1,
            "prompt": "Teach me how user roles work",
            "expected_mode": "TUTOR_QA",
            "check": lambda res: "User Role" in res["response"] and not res["meta"].get("sql_executed")
        },
        {
            "id": 2,
            "prompt": "Generate ER diagram for users and wallet_transaction",
            "expected_mode": "ERD_GEN",
            "check": lambda res: "erDiagram" in res["response"] and "users" in res["response"]
        },
        {
            "id": 3,
            "prompt": "Build a dashboard for July activity",
            "expected_mode": "DASHBOARD_GEN",
            "check": lambda res: res["meta"].get("dashboard_spec") is not None
        },
        {
            "id": 4,
            "prompt": "What happened this month in simple words?",
            "expected_mode": "BUSINESS_STORY",
            "check": lambda res: "Executive Business Story" in res["response"]
        },
        {
            "id": 5,
            "prompt": "Show top 10 retailers by earnings for July 2026",
            "expected_mode": "SQL_ANALYTICS",
            "check": lambda res: res["generated_sql"] != ""
        }
    ]

    passed = 0
    total = len(test_cases)

    for tc in test_cases:
        cid = tc["id"]
        prompt = tc["prompt"]
        exp_mode = tc["expected_mode"]

        print(f"\n[Test {cid}/{total}] Prompt: '{prompt}'")
        classified_mode = route_intent(prompt)
        print(f"  -> Classified Intent: {classified_mode} (Expected: {exp_mode})")

        if classified_mode != exp_mode:
            print(f"  ❌ FAILED: Expected mode {exp_mode}, got {classified_mode}")
            continue

        result = handle_collaborative_query(prompt, execute=True)

        if tc["check"](result):
            print(f"  ✅ PASSED: Handled in {classified_mode} mode successfully.")
            passed += 1
        else:
            print(f"  ❌ FAILED: Verification check failed for output payload.")

    print("\n" + "=" * 70)
    print(f" 📊 FINAL RESULT: {passed}/{total} Test Cases Passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = run_collaborator_tests()
    sys.exit(0 if success else 1)
