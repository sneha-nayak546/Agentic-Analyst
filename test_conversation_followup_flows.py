"""
Dedicated Verification Suite for Conversation Follow-Up Logic & Context Resolution.

Tests the four exact conversational flows:
1. Show Karnataka distributors -> What about their earnings? -> Which one has the highest earnings?
2. Show August withdrawals -> How many were approved? -> What about July?
3. Show distributor ID 12345 -> What are their earnings?
4. Show Karnataka distributors -> Show Kerala distributors -> What about their earnings?

Also verifies that standalone questions clear previous context and that unrelated filters are never carried over.
"""

import sys
import os

from app.agent.context_resolver import context_resolver
from app.agent.memory_manager import memory_manager
from app.agent.query_planner import create_plan
from app.llm.sql_generator import generate_sql
from app.agent.sql_agent import run_agent
from app.agent.intent_router import route_intent
from app.api.main import query_database, QueryRequest

def run_tests():
    print("=" * 80)
    print("  CONVERSATION FOLLOW-UP RESOLUTION TEST SUITE")
    print("=" * 80)

    passed = 0
    failed = 0

    def check(name: str, cond: bool, err_msg: str = ""):
        nonlocal passed, failed
        if cond:
            print(f"  [OK] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name} -> {err_msg}")
            failed += 1

    # =========================================================================
    # FLOW 1: Show Karnataka distributors -> What about their earnings? -> Which one has the highest earnings?
    # =========================================================================
    print("\n--- FLOW 1: Karnataka distributors -> their earnings -> highest earnings ---")
    s1 = "session_flow_1"
    memory_manager.clear_session(s1)

    # Turn 1: Show Karnataka distributors
    ctx1_1 = memory_manager.resolve_session_context(s1, "Show Karnataka distributors")
    check("F1.T1: Entity is distributor", ctx1_1.get("entity") == "distributor", f"got {ctx1_1.get('entity')}")
    check("F1.T1: Role ID is 4", ctx1_1.get("role_id") == 4, f"got {ctx1_1.get('role_id')}")
    check("F1.T1: Region is Karnataka", ctx1_1.get("region") == "Karnataka", f"got {ctx1_1.get('region')}")
    plan1_1 = create_plan("Show Karnataka distributors", context=ctx1_1)
    sql1_1 = generate_sql("", plan=plan1_1)
    check("F1.T1: SQL filters state 29 / Karnataka", "state_id = 29" in sql1_1 or "Karnataka" in sql1_1, f"SQL: {sql1_1}")
    check("F1.T1: SQL filters user_role = 4", "user_role = 4" in sql1_1, f"SQL: {sql1_1}")

    # Turn 2: What about their earnings?
    intent1_2 = route_intent("What about their earnings?")
    check("F1.T2: Intent is SQL_ANALYTICS (not hijacked)", intent1_2 == "SQL_ANALYTICS", f"got {intent1_2}")
    ctx1_2 = memory_manager.resolve_session_context(s1, "What about their earnings?")
    check("F1.T2: Follow-up detected", ctx1_2.get("is_explicit_follow_up") is True)
    check("F1.T2: Entity preserved (distributor)", ctx1_2.get("entity") == "distributor", f"got {ctx1_2.get('entity')}")
    check("F1.T2: Region preserved (Karnataka)", ctx1_2.get("region") == "Karnataka", f"got {ctx1_2.get('region')}")
    check("F1.T2: Metric is earnings", ctx1_2.get("metric") == "earnings", f"got {ctx1_2.get('metric')}")
    plan1_2 = create_plan("What about their earnings?", context=ctx1_2)
    sql1_2 = generate_sql("", plan=plan1_2)
    check("F1.T2: SQL has SUM(wt.amount)", "SUM(wt.amount)" in sql1_2, f"SQL: {sql1_2}")
    check("F1.T2: SQL has wallet_transaction join", "JOIN wallet_transaction" in sql1_2, f"SQL: {sql1_2}")
    check("F1.T2: SQL retains Karnataka filter", "state_id = 29" in sql1_2 or "Karnataka" in sql1_2, f"SQL: {sql1_2}")

    # Turn 3: Which one has the highest earnings?
    intent1_3 = route_intent("Which one has the highest earnings?")
    check("F1.T3: Intent is SQL_ANALYTICS", intent1_3 == "SQL_ANALYTICS", f"got {intent1_3}")
    ctx1_3 = memory_manager.resolve_session_context(s1, "Which one has the highest earnings?")
    check("F1.T3: Follow-up detected", ctx1_3.get("is_explicit_follow_up") is True)
    check("F1.T3: Entity preserved (distributor)", ctx1_3.get("entity") == "distributor", f"got {ctx1_3.get('entity')}")
    check("F1.T3: Region preserved (Karnataka)", ctx1_3.get("region") == "Karnataka", f"got {ctx1_3.get('region')}")
    check("F1.T3: Limit is 1", ctx1_3.get("limit") == 1, f"got {ctx1_3.get('limit')}")
    plan1_3 = create_plan("Which one has the highest earnings?", context=ctx1_3)
    sql1_3 = generate_sql("", plan=plan1_3)
    check("F1.T3: SQL orders by earnings DESC", "ORDER BY total_earnings DESC" in sql1_3, f"SQL: {sql1_3}")
    check("F1.T3: SQL limits to 1", sql1_3.strip().endswith("LIMIT 1;"), f"SQL: {sql1_3}")
    check("F1.T3: SQL retains Karnataka filter", "state_id = 29" in sql1_3 or "Karnataka" in sql1_3, f"SQL: {sql1_3}")

    # =========================================================================
    # FLOW 2: Show August withdrawals -> How many were approved? -> What about July?
    # =========================================================================
    print("\n--- FLOW 2: August withdrawals -> How many approved -> What about July ---")
    s2 = "session_flow_2"
    memory_manager.clear_session(s2)

    # Turn 1: Show August withdrawals
    ctx2_1 = memory_manager.resolve_session_context(s2, "Show August withdrawals")
    check("F2.T1: Entity is withdrawal_request", ctx2_1.get("entity") == "withdrawal_request", f"got {ctx2_1.get('entity')}")
    check("F2.T1: Month is 8 (August)", ctx2_1.get("month") == 8, f"got {ctx2_1.get('month')}")
    plan2_1 = create_plan("Show August withdrawals", context=ctx2_1)
    sql2_1 = generate_sql("", plan=plan2_1)
    check("F2.T1: SQL targets withdrawal_request", "withdrawal_request" in sql2_1, f"SQL: {sql2_1}")
    check("F2.T1: SQL has August 2026 dates", "2026-08-01" in sql2_1, f"SQL: {sql2_1}")

    # Turn 2: How many were approved?
    ctx2_2 = memory_manager.resolve_session_context(s2, "How many were approved?")
    check("F2.T2: Follow-up detected", ctx2_2.get("is_explicit_follow_up") is True)
    check("F2.T2: Entity preserved (withdrawal_request)", ctx2_2.get("entity") == "withdrawal_request", f"got {ctx2_2.get('entity')}")
    check("F2.T2: Month preserved (8 / August)", ctx2_2.get("month") == 8, f"got {ctx2_2.get('month')}")
    check("F2.T2: Status filter is approved", ctx2_2.get("status_filter") == "approved", f"got {ctx2_2.get('status_filter')}")
    check("F2.T2: Metric is count", ctx2_2.get("metric") == "count", f"got {ctx2_2.get('metric')}")
    plan2_2 = create_plan("How many were approved?", context=ctx2_2)
    sql2_2 = generate_sql("", plan=plan2_2)
    check("F2.T2: SQL has COUNT(*)", "COUNT(*)" in sql2_2, f"SQL: {sql2_2}")
    check("F2.T2: SQL filters wr.status = 1 (approved)", "wr.status = 1" in sql2_2, f"SQL: {sql2_2}")
    check("F2.T2: SQL retains August date range", "2026-08-01" in sql2_2, f"SQL: {sql2_2}")

    # Turn 3: What about July?
    ctx2_3 = memory_manager.resolve_session_context(s2, "What about July?")
    check("F2.T3: Follow-up detected", ctx2_3.get("is_explicit_follow_up") is True)
    check("F2.T3: Entity preserved (withdrawal_request)", ctx2_3.get("entity") == "withdrawal_request", f"got {ctx2_3.get('entity')}")
    check("F2.T3: Month updated to 7 (July)", ctx2_3.get("month") == 7, f"got {ctx2_3.get('month')}")
    check("F2.T3: Status filter preserved (approved)", ctx2_3.get("status_filter") == "approved", f"got {ctx2_3.get('status_filter')}")
    plan2_3 = create_plan("What about July?", context=ctx2_3)
    sql2_3 = generate_sql("", plan=plan2_3)
    check("F2.T3: SQL filters wr.status = 1", "wr.status = 1" in sql2_3, f"SQL: {sql2_3}")
    check("F2.T3: SQL updated to July dates (2026-07-01)", "2026-07-01" in sql2_3, f"SQL: {sql2_3}")
    check("F2.T3: SQL starts from July, not August", "wr.created_at >= '2026-07-01" in sql2_3 and "wr.created_at >= '2026-08-01" not in sql2_3, f"SQL: {sql2_3}")

    # =========================================================================
    # FLOW 3: Show distributor ID 12345 -> What are their earnings?
    # =========================================================================
    print("\n--- FLOW 3: Show distributor ID 12345 -> What are their earnings? ---")
    s3 = "session_flow_3"
    memory_manager.clear_session(s3)

    # Turn 1: Show distributor ID 12345
    ctx3_1 = memory_manager.resolve_session_context(s3, "Show distributor ID 12345")
    check("F3.T1: Specific ID is 12345", str(ctx3_1.get("specific_id")) == "12345", f"got {ctx3_1.get('specific_id')}")
    check("F3.T1: Entity is distributor", ctx3_1.get("entity") == "distributor", f"got {ctx3_1.get('entity')}")

    # Turn 2: What are their earnings?
    intent3_2 = route_intent("What are their earnings?")
    check("F3.T2: Intent is SQL_ANALYTICS", intent3_2 == "SQL_ANALYTICS", f"got {intent3_2}")
    ctx3_2 = memory_manager.resolve_session_context(s3, "What are their earnings?")
    check("F3.T2: Follow-up detected", ctx3_2.get("is_explicit_follow_up") is True)
    check("F3.T2: Specific ID preserved (12345)", str(ctx3_2.get("specific_id")) == "12345", f"got {ctx3_2.get('specific_id')}")
    check("F3.T2: Metric is earnings", ctx3_2.get("metric") == "earnings", f"got {ctx3_2.get('metric')}")
    plan3_2 = create_plan("What are their earnings?", context=ctx3_2)
    sql3_2 = generate_sql("", plan=plan3_2)
    check("F3.T2: SQL computes SUM(wt.amount)", "SUM(wt.amount)" in sql3_2, f"SQL: {sql3_2}")
    check("F3.T2: SQL filters by u.id = 12345", "u.id = 12345" in sql3_2, f"SQL: {sql3_2}")
    check("F3.T2: SQL joins wallet_transaction", "JOIN wallet_transaction" in sql3_2, f"SQL: {sql3_2}")

    # =========================================================================
    # FLOW 4: Show Karnataka distributors -> Show Kerala distributors -> What about their earnings?
    # =========================================================================
    print("\n--- FLOW 4: Karnataka -> Kerala -> What about their earnings? ---")
    s4 = "session_flow_4"
    memory_manager.clear_session(s4)

    # Turn 1: Show Karnataka distributors
    ctx4_1 = memory_manager.resolve_session_context(s4, "Show Karnataka distributors")
    check("F4.T1: Region is Karnataka", ctx4_1.get("region") == "Karnataka", f"got {ctx4_1.get('region')}")

    # Turn 2: Show Kerala distributors (Update region filter)
    ctx4_2 = memory_manager.resolve_session_context(s4, "Show Kerala distributors")
    check("F4.T2: Region is updated to Kerala", ctx4_2.get("region") == "Kerala", f"got {ctx4_2.get('region')}")
    check("F4.T2: Entity is distributor", ctx4_2.get("entity") == "distributor", f"got {ctx4_2.get('entity')}")
    plan4_2 = create_plan("Show Kerala distributors", context=ctx4_2)
    sql4_2 = generate_sql("", plan=plan4_2)
    check("F4.T2: SQL filters Kerala (state_id = 32)", "state_id = 32" in sql4_2 or "Kerala" in sql4_2, f"SQL: {sql4_2}")
    check("F4.T2: SQL does NOT contain Karnataka / state 29", "state_id = 29" not in sql4_2 and "Karnataka" not in sql4_2, f"SQL: {sql4_2}")

    # Turn 3: What about their earnings?
    ctx4_3 = memory_manager.resolve_session_context(s4, "What about their earnings?")
    check("F4.T3: Follow-up detected", ctx4_3.get("is_explicit_follow_up") is True)
    check("F4.T3: Region is Kerala (not Karnataka)", ctx4_3.get("region") == "Kerala", f"got {ctx4_3.get('region')}")
    check("F4.T3: Entity is distributor", ctx4_3.get("entity") == "distributor", f"got {ctx4_3.get('entity')}")
    check("F4.T3: Metric is earnings", ctx4_3.get("metric") == "earnings", f"got {ctx4_3.get('metric')}")
    plan4_3 = create_plan("What about their earnings?", context=ctx4_3)
    sql4_3 = generate_sql("", plan=plan4_3)
    check("F4.T3: SQL computes earnings for Kerala distributors", "state_id = 32" in sql4_3 or "Kerala" in sql4_3, f"SQL: {sql4_3}")
    check("F4.T3: SQL does NOT contain Karnataka / state 29", "state_id = 29" not in sql4_3 and "Karnataka" not in sql4_3, f"SQL: {sql4_3}")

    # =========================================================================
    # FLOW 5: Standalone question clearing validation
    # =========================================================================
    print("\n--- FLOW 5: Standalone questions clearing stale context ---")
    s5 = "session_flow_5"
    memory_manager.clear_session(s5)

    # Base turn
    memory_manager.resolve_session_context(s5, "Show Karnataka distributors for July 2026")
    # Standalone turn
    ctx5_standalone = memory_manager.resolve_session_context(s5, "Show total withdrawals")
    check("F5.1: Karnataka cleared on standalone", ctx5_standalone.get("region") is None, f"got {ctx5_standalone.get('region')}")
    check("F5.2: July 2026 cleared on standalone", ctx5_standalone.get("period") is None, f"got {ctx5_standalone.get('period')}")
    check("F5.3: Entity is withdrawal_request", ctx5_standalone.get("entity") == "withdrawal_request", f"got {ctx5_standalone.get('entity')}")

    # =========================================================================
    # FLOW 6: Full API Endpoint Simulation via query_database
    # =========================================================================
    print("\n--- FLOW 6: Full API multi-turn execution simulation ---")
    api_session = "api_test_session_1"
    memory_manager.clear_session(api_session)

    # API Turn 1
    res1 = query_database(QueryRequest(question="Show Karnataka distributors", session_id=api_session))
    check("API.1: Turn 1 status is success", res1.get("status") == "success")
    check("API.1: Turn 1 SQL filters state_id = 29", "state_id = 29" in res1.get("sql_query", "") or "Karnataka" in res1.get("sql_query", ""))

    # API Turn 2
    res2 = query_database(QueryRequest(question="What about their earnings?", session_id=api_session))
    check("API.2: Turn 2 status is success", res2.get("status") == "success")
    check("API.2: Turn 2 SQL computes total earnings", "SUM(wt.amount)" in res2.get("sql_query", ""))
    check("API.2: Turn 2 SQL retains Karnataka", "state_id = 29" in res2.get("sql_query", "") or "Karnataka" in res2.get("sql_query", ""))

    # API Turn 3
    res3 = query_database(QueryRequest(question="Which one has the highest earnings?", session_id=api_session))
    check("API.3: Turn 3 status is success", res3.get("status") == "success")
    sql_3_res = res3.get("sql_query", "").strip()
    check("API.3: Turn 3 SQL limits to 1", sql_3_res.endswith("LIMIT 1") or sql_3_res.endswith("LIMIT 1;"), f"SQL: {sql_3_res}")
    check("API.3: Turn 3 SQL retains Karnataka", "state_id = 29" in sql_3_res or "Karnataka" in sql_3_res, f"SQL: {sql_3_res}")

    print("\n" + "=" * 80)
    print(f"  RESULTS: {passed} PASSED, {failed} FAILED out of {passed + failed} checks")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
