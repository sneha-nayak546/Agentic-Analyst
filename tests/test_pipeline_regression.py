"""
Comprehensive Regression Test for Pipeline Fixes.
Tests:
  1. 15+ natural language questions across all entity types
  2. Follow-up / context inheritance and override
  3. Wrong ID + similar ID suggestions
  4. Date/month variations
  5. Entity variations (distributors, retailers, wholesalers, mechanics, withdrawals, inventory, earnings)
  6. Two independent sessions with no cross-leakage
  7. New unrelated question after context — stale filters must be cleared
"""

import sys
import json
import re

# Fix Windows encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# Add project root to path
sys.path.insert(0, ".")

from app.agent.context_resolver import context_resolver, ContextResolver
from app.agent.query_planner import create_plan
from app.llm.sql_generator import generate_sql, _synthesize_sql_from_plan
from app.agent.memory_manager import MemoryManager
from app.utils.date_parser import parse_temporal_expressions
from app.agent.id_search import extract_id_from_prompt

PASS = 0
FAIL = 0
RESULTS = []

def check(test_name, condition, detail=""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    RESULTS.append({"test": test_name, "status": status, "detail": detail})
    icon = "OK" if condition else "XX"
    print(f"  [{icon}] {test_name}" + (f" -- {detail}" if detail and not condition else ""))


def sql_has_filter(sql, filter_text):
    """Check if SQL contains a filter string (case-insensitive)."""
    return filter_text.lower() in sql.lower()


def sql_missing_filter(sql, filter_text):
    """Check that SQL does NOT contain a filter string."""
    return filter_text.lower() not in sql.lower()


print("=" * 80)
print("  PIPELINE REGRESSION TESTS")
print("=" * 80)

# ============================================================================
# TEST GROUP 1: Context Resolver — Stale Context Clearing
# ============================================================================
print("\n--- GROUP 1: Context Resolver — Stale Context Clearing ---")

# Turn 1: Karnataka distributors
ctx1 = context_resolver.resolve("Show Karnataka distributors")
check("T1.1: Karnataka detected",
      ctx1.get("region") == "Karnataka",
      f"got region={ctx1.get('region')}")
check("T1.2: Distributor detected",
      ctx1.get("entity") == "distributor",
      f"got entity={ctx1.get('entity')}")

# Turn 2: New standalone question — NO follow-up cues
ctx2 = context_resolver.resolve("Show total withdrawals", previous_context=ctx1)
check("T1.3: Withdrawal entity detected",
      ctx2.get("entity") == "withdrawal_request",
      f"got entity={ctx2.get('entity')}")
check("T1.4: Karnataka NOT inherited (standalone)",
      ctx2.get("region") is None,
      f"got region={ctx2.get('region')}")
check("T1.5: Distributor role NOT inherited",
      ctx2.get("role_id") is None,
      f"got role_id={ctx2.get('role_id')}")

# Turn 3: Explicit follow-up — SHOULD inherit
ctx3 = context_resolver.resolve("Show their earnings", previous_context=ctx1)
check("T1.6: Follow-up inherits Karnataka",
      ctx3.get("region") == "Karnataka",
      f"got region={ctx3.get('region')}")
check("T1.7: Follow-up inherits distributor",
      ctx3.get("entity") == "distributor",
      f"got entity={ctx3.get('entity')}")

# Turn 4: New question with its own filters
ctx4 = context_resolver.resolve("Show retailers in Maharashtra for August 2026", previous_context=ctx1)
check("T1.8: Maharashtra overrides Karnataka",
      ctx4.get("region") == "Maharashtra",
      f"got region={ctx4.get('region')}")
check("T1.9: Retailer overrides distributor",
      ctx4.get("entity") == "retailer",
      f"got entity={ctx4.get('entity')}")

# Turn 5: New question with NO filters at all
ctx5 = context_resolver.resolve("Show total earnings", previous_context=ctx1)
check("T1.10: No stale region on standalone",
      ctx5.get("region") is None,
      f"got region={ctx5.get('region')}")
check("T1.11: No stale time on standalone",
      ctx5.get("time_condition") is None,
      f"got time_condition={ctx5.get('time_condition')}")

# Turn 6: Question after temporal context
ctx_time = context_resolver.resolve("Show Karnataka distributors for July 2026")
ctx_after = context_resolver.resolve("How many retailers are there?", previous_context=ctx_time)
check("T1.12: July 2026 NOT inherited (standalone)",
      ctx_after.get("period") is None and ctx_after.get("time_condition") is None,
      f"got period={ctx_after.get('period')}, time_condition={ctx_after.get('time_condition')}")
check("T1.13: Karnataka NOT inherited (standalone)",
      ctx_after.get("region") is None,
      f"got region={ctx_after.get('region')}")

# ============================================================================
# TEST GROUP 2: SQL Generation — No Fabricated Filters
# ============================================================================
print("\n--- GROUP 2: SQL Generation — No Fabricated Filters ---")

questions_no_filters = [
    ("Show total withdrawals", ["lucknow", "karnataka", "july", "user_role"]),
    ("How many retailers are there?", ["lucknow", "karnataka", "july"]),
    ("Show total earnings", ["lucknow", "karnataka", "july"]),
    ("List all companies", ["lucknow", "karnataka", "july", "user_role"]),
]

for i, (question, forbidden) in enumerate(questions_no_filters, 1):
    ctx = context_resolver.resolve(question)
    plan = create_plan(question, context=ctx)
    sql = _synthesize_sql_from_plan(plan) or ""
    for f_text in forbidden:
        check(f"T2.{i}: '{question}' has no '{f_text}'",
              sql_missing_filter(sql, f_text),
              f"SQL: {sql[:120]}...")


# ============================================================================
# TEST GROUP 3: SQL Generation — Correct Filters When Specified
# ============================================================================
print("\n--- GROUP 3: SQL Generation — Correct Filters When Specified ---")

test_cases_with_filters = [
    ("Show Karnataka distributors", {"user_role = 4": True, "state_id = 29": True}),
    ("List retailers in Maharashtra", {"user_role = 2": True, "state_id = 27": True}),
    ("Show distributor earnings for August 2026", {"user_role = 4": True, "2026-08-01": True}),
    ("Show wholesalers", {"user_role = 5": True}),
    ("Show wallet transactions for January 2026", {"2026-01-01": True}),
    ("Show total withdrawals", {"withdrawal_request": True}),
    ("How many distributors are in Kerala?", {"user_role = 4": True, "state_id = 32": True, "count": True}),
    ("Show inventory data", {"sku_inventories": True}),
]

for i, (question, expected) in enumerate(test_cases_with_filters, 1):
    ctx = context_resolver.resolve(question)
    plan = create_plan(question, context=ctx)
    sql = _synthesize_sql_from_plan(plan) or ""
    for filter_text, should_be_present in expected.items():
        if should_be_present:
            check(f"T3.{i}: '{question}' has '{filter_text}'",
                  sql_has_filter(sql, filter_text),
                  f"SQL: {sql[:150]}...")

# ============================================================================
# TEST GROUP 4: Date/Month Parsing
# ============================================================================
print("\n--- GROUP 4: Date/Month Parsing ---")

date_tests = [
    ("Aug", True, 8),
    ("Aug 2026", True, 8),
    ("August 2026", True, 8),
    ("last month", True, 7),  # current month is Aug 2026
    ("this month", True, 8),
    ("July", True, 7),
    ("July 2026", True, 7),
    ("Q1", True, None),
    ("today", True, None),
    ("yesterday", True, None),
    ("Show data", False, None),
]

for i, (text, expect_time, expect_month) in enumerate(date_tests, 1):
    result = parse_temporal_expressions(text)
    check(f"T4.{i}: '{text}' has_time_filter={expect_time}",
          result.get("has_time_filter") == expect_time,
          f"got has_time_filter={result.get('has_time_filter')}")
    if expect_month:
        check(f"T4.{i}b: '{text}' month={expect_month}",
              result.get("month") == expect_month,
              f"got month={result.get('month')}")


# ============================================================================
# TEST GROUP 5: ID Extraction
# ============================================================================
print("\n--- GROUP 5: ID Extraction ---")

id_tests = [
    ("Show distributor 12345", True, "12345", "distributor"),
    ("Show retailer ID 46556", True, "46556", "retailer"),
    ("Details of ID 5842", True, "5842", "user"),
    ("Show total earnings", False, None, None),
    ("How many retailers?", False, None, None),
]

for i, (prompt, expect_id, expected_raw, expected_entity) in enumerate(id_tests, 1):
    result = extract_id_from_prompt(prompt)
    if expect_id:
        check(f"T5.{i}: '{prompt}' extracts ID",
              result is not None and result.get("raw_id") == expected_raw,
              f"got {result}")
    else:
        check(f"T5.{i}: '{prompt}' is NOT an ID query",
              result is None,
              f"got {result}")


# ============================================================================
# TEST GROUP 6: Session Isolation (Two independent sessions)
# ============================================================================
print("\n--- GROUP 6: Session Isolation ---")

mm = MemoryManager()

# Session A: Karnataka distributors
ctx_a1 = mm.resolve_session_context("session_A", "Show Karnataka distributors for July 2026")
check("T6.1: Session A has Karnataka",
      ctx_a1.get("region") == "Karnataka",
      f"got {ctx_a1.get('region')}")

# Session B: Maharashtra retailers (completely independent)
ctx_b1 = mm.resolve_session_context("session_B", "Show Maharashtra retailers")
check("T6.2: Session B has Maharashtra",
      ctx_b1.get("region") == "Maharashtra",
      f"got {ctx_b1.get('region')}")
check("T6.3: Session B has retailer",
      ctx_b1.get("entity") == "retailer",
      f"got {ctx_b1.get('entity')}")

# Verify Session A context is not contaminated by Session B
ctx_a2 = mm.get_session_context("session_A")
check("T6.4: Session A still has Karnataka (not Maharashtra)",
      ctx_a2.get("region") == "Karnataka",
      f"got {ctx_a2.get('region')}")
check("T6.5: Session A still has distributor (not retailer)",
      ctx_a2.get("entity") == "distributor",
      f"got {ctx_a2.get('entity')}")

# Session A: New unrelated question
ctx_a3 = mm.resolve_session_context("session_A", "Show total withdrawals")
check("T6.6: Session A standalone clears Karnataka",
      ctx_a3.get("region") is None,
      f"got region={ctx_a3.get('region')}")
check("T6.7: Session A standalone clears July 2026",
      ctx_a3.get("period") is None,
      f"got period={ctx_a3.get('period')}")

# Session B should be unaffected
ctx_b2 = mm.get_session_context("session_B")
check("T6.8: Session B unaffected by Session A",
      ctx_b2.get("region") == "Maharashtra",
      f"got {ctx_b2.get('region')}")

mm.clear_session("session_A")
mm.clear_session("session_B")


# ============================================================================
# TEST GROUP 7: Entity Variations (all 10 tables)
# ============================================================================
print("\n--- GROUP 7: Entity Variations ---")

entity_questions = [
    ("Show all distributors", "user_role = 4"),
    ("Show all retailers", "user_role = 2"),
    ("Show all wholesalers", "user_role = 5"),
    ("Show mechanics", "mechanic"),
    ("Show withdrawals", "withdrawal_request"),
    ("Show inventory", "sku_inventories"),
    ("Show all companies", "companies"),
    ("Show wallet transactions", "wallet_transaction"),
]

for i, (question, expected_table_or_filter) in enumerate(entity_questions, 1):
    ctx = context_resolver.resolve(question)
    plan = create_plan(question, context=ctx)
    sql = _synthesize_sql_from_plan(plan) or ""
    check(f"T7.{i}: '{question}' → has '{expected_table_or_filter}'",
          sql_has_filter(sql, expected_table_or_filter),
          f"SQL: {sql[:150]}...")


# ============================================================================
# TEST GROUP 8: Follow-up Context (What about retailers?)
# ============================================================================
print("\n--- GROUP 8: Follow-up Context ---")

mm2 = MemoryManager()

# Turn 1: Show Karnataka distributors
ctx_f1 = mm2.resolve_session_context("follow_test", "Show Karnataka distributors")
check("T8.1: Base context has Karnataka+distributor",
      ctx_f1.get("region") == "Karnataka" and ctx_f1.get("entity") == "distributor",
      f"got region={ctx_f1.get('region')}, entity={ctx_f1.get('entity')}")

# Turn 2: "What about their earnings?" — explicit follow-up
ctx_f2 = mm2.resolve_session_context("follow_test", "What about their earnings?")
check("T8.2: Follow-up inherits Karnataka",
      ctx_f2.get("region") == "Karnataka",
      f"got region={ctx_f2.get('region')}")
check("T8.3: Follow-up inherits distributor",
      ctx_f2.get("entity") == "distributor",
      f"got entity={ctx_f2.get('entity')}")
check("T8.4: Follow-up has earnings metric",
      ctx_f2.get("metric") == "earnings",
      f"got metric={ctx_f2.get('metric')}")

mm2.clear_session("follow_test")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print(f"  RESULTS: {PASS} PASSED, {FAIL} FAILED out of {PASS + FAIL} tests")
print("=" * 80)

if FAIL > 0:
    print("\nFAILED TESTS:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"  ✗ {r['test']}: {r['detail']}")

sys.exit(0 if FAIL == 0 else 1)
