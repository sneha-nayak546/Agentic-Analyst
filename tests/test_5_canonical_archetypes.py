"""
The 5 Canonical Question Archetypes Golden Test Suite for JGH Intelligence Engine.
Tests the 5 core business question archetypes:
1. Simple Listing: "Show all retailers"
2. Relationship Mapping: "Generate a table of retailers linked to distributor 5997"
3. Scalar Aggregation: "Show total wallet amount for July 2026"
4. Period Comparison: "Compare total wallet transactions between July and June 2026"
5. Top-N Ranking: "Show top 10 retailers by earnings for July 2026"
"""

import sys
import os
import pytest

# Ensure utf-8 stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.sql_agent import run_agent


def test_archetype_1_simple_listing():
    """Archetype 1: Simple Entity Listing."""
    q = "Show all retailers"
    res = run_agent(q)

    print(f"\n[Archetype 1: {q}]")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    print(f"SQL: {res.get('sql_query') or res.get('generated_sql')}")
    print(f"Row count: {res.get('row_count')}")

    assert res.get("status") in ["VERIFIED", "success", "completed"]
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL"]
    assert res.get("row_count", 0) > 0


def test_archetype_2_relationship_mapping():
    """Archetype 2: Relationship Mapping."""
    q = "Generate a table of retailers linked to distributor 5997"
    res = run_agent(q)

    print(f"\n[Archetype 2: {q}]")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    sql = res.get("sql_query") or res.get("generated_sql") or ""
    print(f"SQL: {sql}")
    print(f"Row count: {res.get('row_count')}")

    assert res.get("status") in ["VERIFIED", "success", "completed"]
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL"]
    assert "phone" not in sql.lower() or "mobile_number" in sql.lower()
    assert res.get("row_count", 0) > 0


def test_archetype_3_scalar_aggregation():
    """Archetype 3: Scalar Aggregation."""
    q = "Show total wallet amount for July 2026"
    res = run_agent(q)

    print(f"\n[Archetype 3: {q}]")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    print(f"SQL: {res.get('sql_query') or res.get('generated_sql')}")
    print(f"Row count: {res.get('row_count')}")

    assert res.get("status") in ["VERIFIED", "success", "completed"]
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL"]
    assert res.get("row_count") == 1


def test_archetype_4_period_comparison():
    """Archetype 4: Period Comparison."""
    q = "Compare total wallet transactions between July and June 2026"
    res = run_agent(q)

    print(f"\n[Archetype 4: {q}]")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    print(f"SQL: {res.get('sql_query') or res.get('generated_sql')}")
    print(f"Row count: {res.get('row_count')}")

    assert res.get("status") in ["VERIFIED", "success", "completed"]
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL"]
    # Comparison can be represented as multiple period rows (>=2 rows) or pivoted period columns (1 row with >=2 metric columns)
    assert res.get("row_count", 0) >= 2 or (res.get("row_count") == 1 and len(res.get("data", [{}])[0]) >= 2)


def test_archetype_5_top_n_ranking():
    """Archetype 5: Top-N Ranking with Partial Count Handling."""
    q = "Show top 10 retailers by earnings for July 2026"
    res = run_agent(q)

    print(f"\n[Archetype 5: {q}]")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    print(f"SQL: {res.get('sql_query') or res.get('generated_sql')}")
    print(f"Row count: {res.get('row_count')}")

    assert res.get("status") in ["VERIFIED", "success", "completed"]
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL"]
    assert res.get("row_count") == 2
