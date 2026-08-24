"""
Test Suite for Exact ID / Identifier Search and Nearest Suggestion Engine.
Tests against the live backend server and MySQL database.
"""

import sys
import json
import urllib.request
import uuid

API_BASE = "http://localhost:8000"

def send_query(question: str, session_id: str = "id_test_sess") -> dict:
    url = f"{API_BASE}/query"
    payload = {
        "question": question,
        "session_id": session_id,
        "user_id": "test_user",
        "execute": True,
        "bypass_cache": True
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_tests():
    print("\n" + "=" * 80)
    print("STARTING EXACT ID / IDENTIFIER SEARCH TEST SUITE")
    print("=" * 80 + "\n")

    results = {}

    # TEST 1: Exact Existing Distributor ID 46965
    print(">>> TEST 1: Exact Existing Distributor ID ('Show distributor ID 46965')")
    res1 = send_query("Show distributor ID 46965")
    rows1 = res1.get("results", [])
    summary1 = res1.get("summary", "")
    print(f"    Summary: {summary1[:120]}...")
    t1_pass = len(rows1) == 1 and rows1[0].get("user_id") == 46965 and rows1[0].get("user_role") == 4
    print(f"    Result: {'[PASS]' if t1_pass else '[FAIL]'}\n")
    results["TEST 1 (Exact Distributor ID 46965)"] = t1_pass

    # TEST 2: Exact Existing Retailer ID 46556
    print(">>> TEST 2: Exact Existing Retailer ID ('Give details for retailer ID 46556')")
    res2 = send_query("Give details for retailer ID 46556")
    rows2 = res2.get("results", [])
    summary2 = res2.get("summary", "")
    print(f"    Summary: {summary2[:120]}...")
    t2_pass = len(rows2) == 1 and rows2[0].get("user_id") == 46556 and rows2[0].get("user_role") == 2
    print(f"    Result: {'[PASS]' if t2_pass else '[FAIL]'}\n")
    results["TEST 2 (Exact Retailer ID 46556)"] = t2_pass

    # TEST 3: Show Customer 46578
    print(">>> TEST 3: Show Customer 46578 ('Show customer 46578')")
    res3 = send_query("Show customer 46578")
    rows3 = res3.get("results", [])
    print(f"    Summary: {res3.get('summary', '')[:120]}...")
    t3_pass = len(rows3) == 1 and rows3[0].get("user_id") == 46578
    print(f"    Result: {'[PASS]' if t3_pass else '[FAIL]'}\n")
    results["TEST 3 (Show Customer 46578)"] = t3_pass

    # TEST 4: Find Distributor 47017
    print(">>> TEST 4: Find Distributor 47017 ('Find distributor 47017')")
    res4 = send_query("Find distributor 47017")
    rows4 = res4.get("results", [])
    print(f"    Summary: {res4.get('summary', '')[:120]}...")
    t4_pass = len(rows4) == 1 and rows4[0].get("user_id") == 47017
    print(f"    Result: {'[PASS]' if t4_pass else '[FAIL]'}\n")
    results["TEST 4 (Find Distributor 47017)"] = t4_pass

    # TEST 5: Generic ID Lookup ('Give me details of ID 47019')
    print(">>> TEST 5: Generic ID ('Give me details of ID 47019')")
    res5 = send_query("Give me details of ID 47019")
    rows5 = res5.get("results", [])
    print(f"    Summary: {res5.get('summary', '')[:120]}...")
    t5_pass = len(rows5) == 1 and rows5[0].get("user_id") == 47019
    print(f"    Result: {'[PASS]' if t5_pass else '[FAIL]'}\n")
    results["TEST 5 (Generic ID 47019)"] = t5_pass

    # TEST 6: Non-Existent ID ('Show distributor ID 10299') -> Nearest Suggestions
    print(">>> TEST 6: Non-Existent ID with Suggestions ('Show distributor ID 10299')")
    res6 = send_query("Show distributor ID 10299")
    rows6 = res6.get("results", [])
    summary6 = res6.get("summary", "")
    options6 = res6.get("options", [])
    print(f"    Summary: {summary6}")
    print(f"    Suggested Options: {options6}")
    t6_pass = len(rows6) == 0 and "does not exist" in summary6 and len(options6) > 0
    print(f"    Result: {'[PASS]' if t6_pass else '[FAIL]'}\n")
    results["TEST 6 (Non-Existent ID Nearest Suggestions)"] = t6_pass

    # TEST 7: Invalid ID Format ('Show distributor ID ABC@@123')
    print(">>> TEST 7: Invalid ID Format ('Show distributor ID ABC@@123')")
    res7 = send_query("Show distributor ID ABC@@123")
    summary7 = res7.get("summary", "")
    print(f"    Summary: {summary7}")
    t7_pass = "not a valid" in summary7 and len(res7.get("results", [])) == 0
    print(f"    Result: {'[PASS]' if t7_pass else '[FAIL]'}\n")
    results["TEST 7 (Invalid Format Rejection)"] = t7_pass

    # SUMMARY
    print("=" * 80)
    print("EXACT ID SEARCH TEST SUITE SUMMARY")
    print("=" * 80)
    all_passed = True
    for t_name, passed in results.items():
        status_str = "PASS" if passed else "FAIL"
        print(f"  [{status_str}]  {t_name}")
        if not passed:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print(">>> SUCCESS: ALL EXACT ID SEARCH SCENARIOS PASSED!\n")
    else:
        print(">>> SOME TESTS FAILED.\n")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
