"""
Golden Benchmark Test Suite & Universal Multi-Intent Accuracy Verification Engine.
Runs 25 core business questions across all 5 operational router modes:
  - 5 TUTOR_QA Benchmark Cases
  - 5 ERD_GEN Benchmark Cases
  - 5 DASHBOARD_GEN Benchmark Cases
  - 5 BUSINESS_STORY Benchmark Cases
  - 5 SQL_ANALYTICS Benchmark Cases
Validates output payloads via universal_validator and outputs the overall Accuracy Score (Target: 25/25 Passed = 100%).
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.intent_router import route_intent
from app.agent.collaborator import handle_collaborative_query
from app.validator.universal_validator import universal_validator

BENCHMARK_FILE = PROJECT_ROOT / "tests" / "golden_dataset.json"

def run_accuracy_benchmark():
    print("=" * 75)
    print(" 🏆 JGH AI Collaborator — Universal 25-Case Golden Benchmark Accuracy Suite")
    print("=" * 75)

    if not BENCHMARK_FILE.exists():
        print(f"❌ Error: Benchmark file missing at {BENCHMARK_FILE}")
        return False

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    total = len(cases)

    for tc in cases:
        cid = tc["id"]
        q = tc["question"]
        target_mode = tc["target_mode"]

        print(f"\n[Case {cid:02d}/{total}] Question: \"{q}\"")

        # 1. Intent Classification
        classified = route_intent(q)
        print(f"  -> Intent Router: {classified} (Target: {target_mode})")

        if classified != target_mode:
            print(f"  ❌ FAILED: Intent mismatch (Expected {target_mode}, got {classified})")
            continue

        # 2. Pipeline Execution
        result = handle_collaborative_query(q, execute=False)

        # 3. Universal Multi-Intent Validation Check
        val_res = universal_validator.validate(classified, result, q)
        if val_res["status"] == "BLOCKED":
            print(f"  ❌ FAILED: Universal Gatekeeper blocked response: {val_res['reason']}")
            continue

        print(f"  ✅ PASSED: Handled cleanly & validated in {classified} mode.")
        passed += 1

    accuracy_pct = (passed / total) * 100.0

    print("\n" + "=" * 75)
    print(f" 📊 ACCURACY BENCHMARK SCORE: {passed}/{total} Test Cases Passed ({accuracy_pct:.1f}%)")
    print("=" * 75)

    return passed == total

if __name__ == "__main__":
    success = run_accuracy_benchmark()
    sys.exit(0 if success else 1)
