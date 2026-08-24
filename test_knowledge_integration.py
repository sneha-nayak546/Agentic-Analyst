"""
Test suite verifying the Document-Aware Knowledge Integration for JGH AI Collaborator.
"""

import json
from app.agent.collaborator import handle_collaborative_query
from app.agent.intent_router import route_intent

def run_tests():
    print("=" * 70)
    print("      VERIFYING DOCUMENT-AWARE KNOWLEDGE INTEGRATION")
    print("=" * 70)

    test_queries = [
        ("explain about retailer", "TUTOR_QA"),
        ("tell me about wholesaler", "TUTOR_QA"),
        ("explain about distributor", "TUTOR_QA"),
        ("explain about withdrawal", "TUTOR_QA"),
        ("what is kyc", "TUTOR_QA"),
        ("explain user roles", "TUTOR_QA"),
        ("explain automatic_transactions", "TUTOR_QA"),
        ("Show top 5 retailers by earnings for July 2026", "SQL_ANALYTICS")
    ]

    all_passed = True

    for query, expected_mode in test_queries:
        print(f"\n[TEST QUERY]: \"{query}\"")
        detected_mode = route_intent(query)
        print(f"  -> Intent Router: {detected_mode} (Expected: {expected_mode})")
        assert detected_mode == expected_mode, f"Intent mismatch for '{query}'"

        res = handle_collaborative_query(query, execute=True)
        print(f"  -> Collaborator Mode: {res.get('mode')}")
        print(f"  -> Status: {res.get('status')}")
        
        response_text = res.get("response", "")
        print("  -> Response Preview:")
        for line in response_text.split("\n")[:8]:
            print(f"     {line}")
        print("     ...")

        # Specific assertions
        if query == "explain about retailer":
            assert "Retailer" in response_text
            assert "user_role = 2" in response_text
            assert "QR Box Scans" in response_text
            assert "sku_inventories" in response_text
            print("  [PASSED] Retailer document knowledge verified!")

        elif query == "explain about withdrawal":
            assert "withdrawal_request" in response_text
            assert "automatic_transactions" in response_text
            print("  [PASSED] Withdrawal workflow document knowledge verified!")

        elif query == "what is kyc":
            assert "kyc_status" in response_text
            assert "Digio" in response_text or "Aadhaar" in response_text
            print("  [PASSED] KYC document knowledge verified!")

        elif query == "Show top 5 retailers by earnings for July 2026":
            assert res.get("data") is not None
            assert len(res.get("data", [])) > 0
            print(f"  [PASSED] SQL Analytics verified ({len(res['data'])} rows returned)!")

    print("\n" + "=" * 70)
    print("  [ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY!]")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
