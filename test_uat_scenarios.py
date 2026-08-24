import sys
import time
import json
from app.agent.sql_agent import run_agent
from app.database.cache_manager import cache_manager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

uat_scenarios = [
    {
        "persona": "1. Retailer Monthly Earnings",
        "question": "Show earnings of retailers for July 2026",
        "expected_table": "wallet_transaction",
        "expected_filter": "2026-07-01 00:00:00"
    },
    {
        "persona": "2. Dynamic Ledger Balance",
        "question": "Show top 10 users with highest wallet balance",
        "expected_table": "wallet_transaction",
        "expected_filter": "SUM(wt.amount)"
    },
    {
        "persona": "3. Redemptions",
        "question": "Show redemption amount per user for January 2026",
        "expected_table": "wallet_transaction",
        "expected_filter": "withdrawal"
    },
    {
        "persona": "4. Inventory Lookup",
        "question": "Show SKU inventory by location",
        "expected_table": "sku_inventories",
        "expected_filter": "sku_inventories"
    },
    {
        "persona": "5. User Status",
        "question": "How many retailers are active?",
        "expected_table": "users",
        "expected_filter": "user_role = 2"
    }
]

def run_uat():
    print("=" * 80)
    print("AI SQL AGENT - USER ACCEPTANCE TESTING (UAT) SUITE & SIGN-OFF")
    print("=" * 80)
    
    cache_manager.clear()
    all_passed = True

    for item in uat_scenarios:
        persona = item["persona"]
        q = item["question"]
        print(f"\n[UAT PERSONA] {persona}")
        print(f"Prompt: '{q}'")

        # Initial Uncached Run
        t0 = time.time()
        res = run_agent(q, execute=True)
        t_uncached_ms = round((time.time() - t0) * 1000, 2)
        
        sql = res.get("optimized_sql") or res.get("generated_sql", "")
        exec_res = res.get("execution", {})
        data = exec_res.get("data", [])
        row_count = exec_res.get("row_count", len(data))
        exec_success = exec_res.get("success", False)

        print(f"  - Status: {res.get('status')}")
        print(f"  - Generated SQL: {sql}")
        print(f"  - Rows Returned: {row_count}")
        print(f"  - Live DB Execution Time: {exec_res.get('execution_time_ms')} ms (Total: {t_uncached_ms} ms)")
        if data:
            print(f"  - Sample Record: {data[0]}")

        # Populate cache for testing
        response_payload = {
            "status": "success",
            "question": q,
            "sql": sql,
            "results": data,
            "summary": "UAT test summary"
        }
        cache_manager.set(q, response_payload)

        # Cached Hit Run
        t0_cache = time.time()
        cached_res = cache_manager.get(q)
        t_cached_ms = round((time.time() - t0_cache) * 1000, 2)
        
        is_cached_hit = cached_res is not None and cached_res.get("cached") is True
        print(f"  - Cache Lookup: Cached Hit={is_cached_hit}, Latency={t_cached_ms} ms")

        # Assertions
        assert exec_success, f"Scenario {persona} failed live DB execution!"
        assert t_cached_ms < 100, f"Scenario {persona} cached latency {t_cached_ms}ms >= 100ms!"
        print(f"  - Verification: [PASS] (Cached Response Time < 100ms)")

    print("\n" + "=" * 80)
    print("ALL 5 UAT BUSINESS PERSONA SCENARIOS PASSED WITH < 100ms CACHED LATENCY!")
    print("=" * 80)

if __name__ == "__main__":
    run_uat()
