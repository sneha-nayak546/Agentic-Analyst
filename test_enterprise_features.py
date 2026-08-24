"""
Verification Suite for Enterprise Export Suite, Incognito Privacy Mode, and Schema Drift Detector.
"""

import sys
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from fastapi.testclient import TestClient
from app.api.main import app
from app.database.schema_drift_detector import run_schema_drift_check
from app.sql_history.query_history import HISTORY_FILE, get_query_history

client = TestClient(app)

def run_enterprise_tests():
    print("=" * 70)
    print(" 🧪 JGH Enterprise Features Verification Suite")
    print("=" * 70)

    sample_payload = {
        "columns": ["user_id", "user_role", "wallet_balance"],
        "rows": [
            {"user_id": 101, "user_role": 2, "wallet_balance": 5000},
            {"user_id": 102, "user_role": 4, "wallet_balance": 12500}
        ],
        "title": "July Retailer Balance Export",
        "filename": "Test_Export"
    }

    passed = 0
    total = 5

    # Test 1: CSV Export
    print("\n[Test 1/5] Testing POST /api/export/csv ...")
    res_csv = client.post("/api/export/csv", json=sample_payload)
    if res_csv.status_code == 200 and "text/csv" in res_csv.headers.get("content-type", ""):
        print(f"  ✅ PASSED: Returned 200 OK with CSV attachment ({len(res_csv.content)} bytes).")
        passed += 1
    else:
        print(f"  ❌ FAILED: CSV export failed with status {res_csv.status_code}")

    # Test 2: Excel Export
    print("\n[Test 2/5] Testing POST /api/export/excel ...")
    res_excel = client.post("/api/export/excel", json=sample_payload)
    if res_excel.status_code == 200 and "spreadsheetml" in res_excel.headers.get("content-type", ""):
        print(f"  ✅ PASSED: Returned 200 OK with Excel .xlsx binary stream ({len(res_excel.content)} bytes).")
        passed += 1
    else:
        print(f"  ❌ FAILED: Excel export failed with status {res_excel.status_code}")

    # Test 3: PDF Export
    print("\n[Test 3/5] Testing POST /api/export/pdf ...")
    res_pdf = client.post("/api/export/pdf", json=sample_payload)
    if res_pdf.status_code == 200 and "application/pdf" in res_pdf.headers.get("content-type", ""):
        print(f"  ✅ PASSED: Returned 200 OK with PDF report binary stream ({len(res_pdf.content)} bytes).")
        passed += 1
    else:
        print(f"  ❌ FAILED: PDF export failed with status {res_pdf.status_code}")

    # Test 4: Incognito Privacy Mode (is_private == True)
    print("\n[Test 4/5] Testing Incognito Privacy Controller (is_private: true) ...")
    initial_history_len = len(get_query_history(limit=500))

    res_priv = client.post("/query", json={
        "question": "Teach me how user roles work",
        "execute": True,
        "is_private": True
    })

    final_history_len = len(get_query_history(limit=500))

    if res_priv.status_code == 200 and initial_history_len == final_history_len:
        print(f"  ✅ PASSED: Executed query in Incognito Mode with 0 disk history writes logged.")
        passed += 1
    else:
        print(f"  ❌ FAILED: Incognito mode failed (Initial history: {initial_history_len}, Final: {final_history_len})")

    # Test 5: Schema Drift Check
    print("\n[Test 5/5] Testing Automated Schema Drift Detector ...")
    drift_report = run_schema_drift_check()
    if drift_report.get("status") in ["SYNCHRONIZED", "DRIFT_DETECTED"]:
        print(f"  ✅ PASSED: Schema Drift check completed with status '{drift_report.get('status')}'.")
        passed += 1
    else:
        print(f"  ❌ FAILED: Schema Drift check failed: {drift_report}")

    print("\n" + "=" * 70)
    print(f" 📊 FINAL RESULT: {passed}/{total} Test Cases Passed ({passed/total*100:.1f}%)")
    print("=" * 70)

    return passed == total

if __name__ == "__main__":
    success = run_enterprise_tests()
    sys.exit(0 if success else 1)
