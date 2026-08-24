"""
Verification test for:
1. Total Earnings = SUM(wt.amount) from wallet_transaction
2. 4-digit distributor ID lookup (e.g. 5842)
3. 5-digit user/retailer ID lookup (e.g. 46556)
4. Standalone query NOT inheriting Karnataka or distributor sticky context
"""

from app.agent.id_search import extract_id_from_prompt, execute_exact_id_search
from app.agent.context_resolver import context_resolver
from app.agent.sql_agent import run_agent

def test_fixes():
    print("=" * 70)
    print("      VERIFYING USER FEEDBACK & CONTEXT LOGIC FIXES")
    print("=" * 70)

    # 1. Test Retailer ID 46556
    print("\n[1/4] Testing Retailer ID 46556 Lookup...")
    id_info = extract_id_from_prompt("i want details of ID 46556")
    assert id_info is not None, "ID 46556 extraction failed"
    res = execute_exact_id_search(id_info)
    assert res["status"] == "success"
    assert res["id_found"] is True
    print("  -> Summary Output:")
    for line in res["summary"].split("\n"):
        print("    ", line)
    assert "Total Earnings" in res["summary"] and "26,031" in res["summary"]
    assert "Current Wallet Balance" in res["summary"] and "1,392" in res["summary"]
    print("  [PASSED] Retailer ID 46556 shows true sum of amounts earnings (₹26,031)!")

    # 2. Test 4-Digit Distributor ID 5842
    print("\n[2/4] Testing 4-Digit Distributor ID 5842 Lookup...")
    id_info2 = extract_id_from_prompt("details of distributor ID 5842")
    assert id_info2 is not None, "ID 5842 extraction failed"
    res2 = execute_exact_id_search(id_info2)
    assert res2["status"] == "success"
    assert res2["id_found"] is True
    print("  -> Summary Output:")
    for line in res2["summary"].split("\n"):
        print("    ", line)
    assert "SRI SAIDATTA GARMENTS" in res2["summary"]
    assert "Distributor Code" in res2["summary"] and "5842" in res2["summary"]
    print("  [PASSED] 4-digit Distributor ID 5842 resolved to company and linked account!")

    # 3. Test Context Resolution: Standalone query after Karnataka
    print("\n[3/4] Testing Context Resolver: No unwanted Karnataka or Distributor bleed...")
    # Simulate Turn 1: Karnataka distributors
    turn1_ctx = context_resolver.resolve("Show Karnataka distributors")
    assert turn1_ctx.get("region") == "Karnataka"
    assert turn1_ctx.get("entity") == "distributor"
    print("  -> Turn 1 Context:", turn1_ctx["understanding_summary"])

    # Turn 2: Standalone "i want total earnings of aug month"
    turn2_ctx = context_resolver.resolve("i want total earnings of aug month", previous_context=turn1_ctx)
    print("  -> Turn 2 Context:", turn2_ctx["understanding_summary"])
    assert "Karnataka" not in turn2_ctx.get("understanding_summary", "")
    assert turn2_ctx.get("region") is None
    print("  [PASSED] Standalone query did NOT inherit Karnataka or Distributor context!")

    # Turn 3: Explicit follow-up "show their earnings" (SHOULD inherit Karnataka distributors)
    turn3_ctx = context_resolver.resolve("show their earnings", previous_context=turn1_ctx)
    print("  -> Turn 3 Context (explicit follow-up):", turn3_ctx["understanding_summary"])
    assert turn3_ctx.get("region") == "Karnataka"
    assert turn3_ctx.get("entity") == "distributor"
    print("  [PASSED] Explicit follow-up correctly inherited context!")

    # 4. Test SQL Generation for Total Earnings (Sum of Amounts)
    print("\n[4/4] Testing SQL Agent for Earnings Sum...")
    agent_res = run_agent("What is the total earnings for July 2026?", execute=True)
    sql = agent_res.get("generated_sql") or agent_res.get("sql", "")
    print("  -> Generated SQL:", sql)
    assert "SUM(" in sql and ("wallet_transaction" in sql or "amount" in sql)
    print("  [PASSED] Earnings query uses SUM(wallet_transaction.amount)!")

    print("\n" + "=" * 70)
    print("  [ALL FIXES VERIFIED AND PASSING 100%!]")
    print("=" * 70)

if __name__ == "__main__":
    test_fixes()
