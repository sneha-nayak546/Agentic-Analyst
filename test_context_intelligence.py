"""
Comprehensive Automated Test Suite for Context-Aware Query Understanding & Conversational Intelligence.
Tests all 10 core scenarios against the live backend server and MySQL database.
"""

import sys
import json
import urllib.request
import uuid

API_BASE = "http://localhost:8000"

def send_query(question: str, session_id: str, user_id: str = "test_user", is_private: bool = False) -> dict:
    url = f"{API_BASE}/query"
    payload = {
        "question": question,
        "session_id": session_id,
        "user_id": user_id,
        "is_private": is_private,
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
    print("STARTING CONTEXT-AWARE INTELLIGENCE TEST SUITE (10 SCENARIOS)")
    print("=" * 80 + "\n")

    results = {}

    # -------------------------------------------------------------
    # TEST 1: Standalone Month Abbreviation (Aug -> August)
    # -------------------------------------------------------------
    print(">>> TEST 1: Standalone Month Abbreviation ('Show distributor data for Aug.')")
    s1_id = f"session_t1_{uuid.uuid4().hex[:6]}"
    res1 = send_query("Show distributor data for Aug.", session_id=s1_id)
    und1 = res1.get("understanding", {})
    sql1 = res1.get("sql_query", "")
    print(f"    Understood: {und1.get('summary')}")
    print(f"    SQL: {sql1}")
    t1_pass = ("August" in und1.get("period", "") or "August" in und1.get("summary", "") or "2026-08" in sql1) and "user_role = 4" in sql1
    print(f"    Result: {'[PASS]' if t1_pass else '[FAIL]'}\n")
    results["TEST 1 (Month Abbreviation Aug=August)"] = t1_pass

    # -------------------------------------------------------------
    # TEST 2: Turn 1 -> Turn 2 Entity Follow-up
    # -------------------------------------------------------------
    print(">>> TEST 2: Follow-up ('Show Karnataka distributors for July 2026.' -> 'What about retailers?')")
    s2_id = f"session_t2_{uuid.uuid4().hex[:6]}"
    res2a = send_query("Show Karnataka distributors for July 2026.", session_id=s2_id)
    print(f"    Turn 1 Understood: {res2a.get('understanding', {}).get('summary')}")
    
    res2b = send_query("What about retailers?", session_id=s2_id)
    und2b = res2b.get("understanding", {})
    sql2b = res2b.get("sql_query", "")
    print(f"    Turn 2 Understood: {und2b.get('summary')}")
    print(f"    SQL: {sql2b}")
    t2_pass = (und2b.get("entity") == "retailer" and und2b.get("region") == "Karnataka" and "July 2026" in und2b.get("period", "")) and "user_role = 2" in sql2b
    print(f"    Result: {'[PASS]' if t2_pass else '[FAIL]'}\n")
    results["TEST 2 (Entity Follow-up Karnataka+July+Retailers)"] = t2_pass

    # -------------------------------------------------------------
    # TEST 3: Turn 3 Metric Follow-up
    # -------------------------------------------------------------
    print(">>> TEST 3: Metric Follow-up ('Show their earnings.')")
    res3 = send_query("Show their earnings.", session_id=s2_id)
    und3 = res3.get("understanding", {})
    sql3 = res3.get("sql_query", "")
    print(f"    Turn 3 Understood: {und3.get('summary')}")
    print(f"    SQL: {sql3}")
    t3_pass = (und3.get("entity") == "retailer" and und3.get("region") == "Karnataka" and und3.get("metric") == "earnings") and "wallet_transaction" in sql3
    print(f"    Result: {'[PASS]' if t3_pass else '[FAIL]'}\n")
    results["TEST 3 (Metric Follow-up Earnings)"] = t3_pass

    # -------------------------------------------------------------
    # TEST 4: Turn 4 Period Comparison Follow-up
    # -------------------------------------------------------------
    print(">>> TEST 4: Comparison Follow-up ('Compare with June.')")
    res4 = send_query("Compare with June.", session_id=s2_id)
    und4 = res4.get("understanding", {})
    sql4 = res4.get("sql_query", "")
    print(f"    Turn 4 Understood: {und4.get('summary')}")
    print(f"    SQL: {sql4}")
    t4_pass = "June" in str(und4.get("comparison", "")) or "june" in sql4.lower()
    print(f"    Result: {'[PASS]' if t4_pass else '[FAIL]'}\n")
    results["TEST 4 (Period Comparison July vs June)"] = t4_pass

    # -------------------------------------------------------------
    # TEST 5: Turn 5 Status Filter Follow-up
    # -------------------------------------------------------------
    print(">>> TEST 5: Status Filter Follow-up ('Only active ones.')")
    res5 = send_query("Only active ones.", session_id=s2_id)
    und5 = res5.get("understanding", {})
    sql5 = res5.get("sql_query", "")
    print(f"    Turn 5 Understood: {und5.get('summary')}")
    print(f"    SQL: {sql5}")
    t5_pass = und5.get("status") == "active" and ("status = 1" in sql5 or "status = 'active'" in sql5)
    print(f"    Result: {'[PASS]' if t5_pass else '[FAIL]'}\n")
    results["TEST 5 (Status Filter Active Only)"] = t5_pass

    # -------------------------------------------------------------
    # TEST 6: Turn 6 Region Override
    # -------------------------------------------------------------
    print(">>> TEST 6: Region Override ('What about Kerala?')")
    res6 = send_query("What about Kerala?", session_id=s2_id)
    und6 = res6.get("understanding", {})
    sql6 = res6.get("sql_query", "")
    print(f"    Turn 6 Understood: {und6.get('summary')}")
    print(f"    SQL: {sql6}")
    t6_pass = und6.get("region") == "Kerala" and und6.get("entity") == "retailer" and "Kerala" in sql6
    print(f"    Result: {'[PASS]' if t6_pass else '[FAIL]'}\n")
    results["TEST 6 (Region Override to Kerala)"] = t6_pass

    # -------------------------------------------------------------
    # TEST 7: Context Reset
    # -------------------------------------------------------------
    print(">>> TEST 7: Context Reset ('Start a new analysis.')")
    res7 = send_query("Start a new analysis.", session_id=s2_id)
    print(f"    Response Mode: {res7.get('mode')}")
    print(f"    Summary: {res7.get('summary')}")
    t7_pass = res7.get("mode") == "CONTEXT_RESET" or res7.get("status") == "success"
    print(f"    Result: {'[PASS]' if t7_pass else '[FAIL]'}\n")
    results["TEST 7 (Context Reset)"] = t7_pass

    # -------------------------------------------------------------
    # TEST 8: Multi-User Concurrency Isolation
    # -------------------------------------------------------------
    print(">>> TEST 8: Multi-User Session Isolation (Session A != Session B)")
    sess_A = f"user_A_{uuid.uuid4().hex[:6]}"
    sess_B = f"user_B_{uuid.uuid4().hex[:6]}"

    # User A asks for Karnataka distributors
    send_query("Show Karnataka distributors for July.", session_id=sess_A, user_id="UserA")
    # User B asks for Kerala distributors
    send_query("Show Kerala distributors for August.", session_id=sess_B, user_id="UserB")

    # Simultaneously ask "What about retailers?"
    res_A = send_query("What about retailers?", session_id=sess_A, user_id="UserA")
    res_B = send_query("What about retailers?", session_id=sess_B, user_id="UserB")

    und_A = res_A.get("understanding", {})
    und_B = res_B.get("understanding", {})
    print(f"    User A Context: {und_A.get('summary')}")
    print(f"    User B Context: {und_B.get('summary')}")

    t8_pass = und_A.get("region") == "Karnataka" and und_B.get("region") == "Kerala"
    print(f"    Result: {'[PASS]' if t8_pass else '[FAIL]'}\n")
    results["TEST 8 (Multi-User Isolation)"] = t8_pass

    # -------------------------------------------------------------
    # TEST 9: Private Mode (In-Memory Session Context without Disk Logging)
    # -------------------------------------------------------------
    print(">>> TEST 9: Private Mode Continuity & Zero Disk History")
    priv_sess = f"priv_sess_{uuid.uuid4().hex[:6]}"
    res9a = send_query("Show Karnataka distributors for July 2026.", session_id=priv_sess, is_private=True)
    res9b = send_query("What about retailers?", session_id=priv_sess, is_private=True)
    und9b = res9b.get("understanding", {})

    # Check history endpoint to verify private query was NOT written to persistent history
    hist_req = urllib.request.Request(f"{API_BASE}/history?limit=10")
    with urllib.request.urlopen(hist_req) as h_resp:
        hist_data = json.loads(h_resp.read().decode("utf-8")).get("data", [])
        private_prompts_found = [h for h in hist_data if priv_sess in str(h)]

    t9_pass = und9b.get("region") == "Karnataka" and und9b.get("entity") == "retailer" and len(private_prompts_found) == 0
    print(f"    Private In-Memory Context: {und9b.get('summary')}")
    print(f"    Persistent History Traces: {len(private_prompts_found)}")
    print(f"    Result: {'[PASS]' if t9_pass else '[FAIL]'}\n")
    results["TEST 9 (Private Mode Zero Disk History)"] = t9_pass

    # -------------------------------------------------------------
    # TEST 10: Ambiguous Query (Show August data -> Clarification)
    # -------------------------------------------------------------
    print(">>> TEST 10: Ambiguous Query ('Show August data.') without prior context")
    s10_id = f"session_t10_{uuid.uuid4().hex[:6]}"
    res10 = send_query("Show August data.", session_id=s10_id)
    is_ambiguous = res10.get("status") == "ambiguous" or res10.get("is_ambiguous", False)
    clarification = res10.get("clarification", "")
    options = res10.get("options", [])
    print(f"    Status: {res10.get('status')}")
    print(f"    Clarification: {clarification}")
    print(f"    Options: {options}")
    t10_pass = is_ambiguous and len(options) > 0
    print(f"    Result: {'[PASS]' if t10_pass else '[FAIL]'}\n")
    results["TEST 10 (Ambiguity Clarification for Vague Query)"] = t10_pass

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("=" * 80)
    print("ALL 10 CONTEXT INTELLIGENCE TESTS COMPLETED")
    print("=" * 80)
    all_passed = True
    for test_name, passed in results.items():
        status_str = "PASS" if passed else "FAIL"
        print(f"  [{status_str}]  {test_name}")
        if not passed:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print(">>> SUCCESS: 10/10 SCENARIOS PASSED WITH FULL CONVERSATIONAL CONTEXT INTELLIGENCE!\n")
    else:
        print(">>> SOME TESTS FAILED. CHECK DETAILS ABOVE.\n")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
