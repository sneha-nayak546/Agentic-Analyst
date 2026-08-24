"""
Automated tests for ResultAccuracyValidator.

Tests all 10 required scenarios:
  1. Correct query + records found → VERIFIED_RESULT
  2. Correct query + genuinely zero records → VERIFIED_EMPTY
  3. Wrong region mapping → SUSPICIOUS_RESULT
  4. Wrong entity mapping → SUSPICIOUS_RESULT
  5. Wrong ID filter → SUSPICIOUS_RESULT
  6. Wrong date filter → SUSPICIOUS_RESULT
  7. SQL executes successfully but is logically wrong → SUSPICIOUS_RESULT
  8. Empty result caused by incorrect filter → SUSPICIOUS_RESULT
  9. Follow-up query with inherited correct context → VERIFIED_RESULT
 10. Simple query with no filters → VERIFIED_RESULT (no checks needed)

All tests mock execute_read_query so no real database connection is needed.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app.database.read_executor
from app.validator.result_accuracy_validator import (
    ResultAccuracyValidator,
    VERIFIED_RESULT,
    VERIFIED_EMPTY,
    SUSPICIOUS_RESULT,
    UNABLE_TO_VERIFY,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _exec(data=None, success=True):
    """Build a fake execution_result dict."""
    rows = data or []
    return {"success": success, "data": rows, "columns": list(rows[0].keys()) if rows else [], "row_count": len(rows)}


def _probe_returns(count: int):
    """Mock execute_read_query to return a given probe count."""
    return {"success": True, "data": [{"probe_count": count}], "columns": ["probe_count"], "row_count": 1}


# ── Test Class ─────────────────────────────────────────────────────────────────

class TestResultAccuracyValidator(unittest.TestCase):

    def setUp(self):
        self.v = ResultAccuracyValidator()

    # ── Test 1: Correct query + records found ──────────────────────────────────
    def test_01_correct_query_with_records(self):
        """Correct SQL (has state_id=29 and user_role=4), non-empty result → VERIFIED_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 4 AND state_id = 29 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka"}
        rows = [{"id": 1, "name": "Distributor A"}, {"id": 2, "name": "Distributor B"}]
        result = self.v.validate("Show Karnataka distributors", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], VERIFIED_RESULT, result["issues_found"])
        self.assertEqual(result["issues_found"], [])

    # ── Test 2: Correct query + genuinely zero records ─────────────────────────
    @patch("app.database.read_executor.execute_read_query")
    def test_02_correct_query_genuinely_empty(self, mock_exec):
        """Correct SQL, 0 rows, probe also returns 0 → VERIFIED_EMPTY."""
        mock_exec.return_value = _probe_returns(0)
        sql = "SELECT * FROM users WHERE user_role = 4 AND state_id = 29 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka"}
        result = self.v.validate("Show Karnataka distributors", sql, ctx, _exec([]))
        self.assertEqual(result["result_confidence"], VERIFIED_EMPTY, result["issues_found"])
        self.assertTrue(result["probe_performed"])
        self.assertEqual(result["probe_result"]["probe_count"], 0)

    # ── Test 3: Wrong region mapping ──────────────────────────────────────────
    def test_03_wrong_region_mapping(self):
        """SQL uses wrong state_id (e.g. 27=Maharashtra instead of 29=Karnataka) → SUSPICIOUS_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 4 AND state_id = 27 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka"}
        rows = [{"id": 1, "name": "Distributor X"}]  # rows returned but wrong region
        result = self.v.validate("Show Karnataka distributors", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertTrue(any("state_id" in issue for issue in result["issues_found"]))

    # ── Test 4: Wrong entity mapping ──────────────────────────────────────────
    def test_04_wrong_entity_mapping(self):
        """SQL uses wrong user_role (e.g. role=2=retailer instead of 4=distributor) → SUSPICIOUS_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 2 AND state_id = 29 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka"}
        rows = [{"id": 1, "name": "Retailer X"}]
        result = self.v.validate("Show Karnataka distributors", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertTrue(any("user_role" in issue for issue in result["issues_found"]))

    # ── Test 5: Wrong ID filter ────────────────────────────────────────────────
    def test_05_wrong_id_filter(self):
        """SQL does not contain the requested specific_id → SUSPICIOUS_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 4 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "specific_id": "46965"}
        rows = [{"id": 99999, "name": "Wrong User"}]
        result = self.v.validate("Show distributor ID 46965", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertTrue(any("46965" in issue for issue in result["issues_found"]))

    # ── Test 6: Wrong date / missing date filter ───────────────────────────────
    def test_06_missing_date_filter(self):
        """User asked for July data but SQL has no date filter → SUSPICIOUS_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 4 AND state_id = 29 LIMIT 100"
        ctx = {
            "entity": "distributor", "role_id": 4, "region": "Karnataka",
            "period": "July 2026", "month": 7, "year": 2026,
            "time_condition": "MONTH(created_at) = 7 AND YEAR(created_at) = 2026"
        }
        rows = [{"id": 1, "name": "Distributor A"}]
        result = self.v.validate("Show Karnataka distributors for July 2026", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertTrue(any("date" in issue.lower() for issue in result["issues_found"]))

    # ── Test 7: SQL executes but is logically wrong (wrong role + wrong state) ─
    def test_07_sql_runs_but_logically_wrong(self):
        """SQL runs and returns rows, but uses both wrong role AND wrong state → SUSPICIOUS_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 2 AND state_id = 27 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka"}
        # Even though rows were returned, the filters are wrong
        rows = [{"id": 1, "name": "Wrong Entity Wrong Region"}]
        result = self.v.validate("Show Karnataka distributors", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertGreaterEqual(len(result["issues_found"]), 2)

    # ── Test 8: Empty result caused by incorrect filter ────────────────────────
    @patch("app.database.read_executor.execute_read_query")
    def test_08_empty_result_wrong_filter_caught_by_probe(self, mock_exec):
        """SQL has correct-looking filters but 0 rows; probe finds records → SUSPICIOUS_RESULT."""
        # Probe returns 50 records — data exists, but main query returned nothing
        mock_exec.return_value = _probe_returns(50)
        sql = "SELECT * FROM users WHERE user_role = 4 AND state_id = 29 AND some_bad_filter = 'xyz' LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka"}
        result = self.v.validate("Show Karnataka distributors", sql, ctx, _exec([]))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertTrue(result["probe_performed"])
        self.assertEqual(result["probe_result"]["probe_count"], 50)
        self.assertTrue(any("probe" in issue.lower() or "50" in issue for issue in result["issues_found"]))

    # ── Test 9: Follow-up question with inherited correct context ──────────────
    def test_09_follow_up_correct_context(self):
        """Follow-up query inherits correct Karnataka+distributor context → VERIFIED_RESULT."""
        sql = "SELECT SUM(wt.amount) FROM wallet_transaction wt JOIN users u ON u.id = wt.user_id WHERE u.user_role = 4 AND u.state_id = 29 LIMIT 100"
        ctx = {
            "entity": "distributor", "role_id": 4, "region": "Karnataka",
            "metric": "earnings", "is_explicit_follow_up": True
        }
        rows = [{"total_earnings": 580000.0}]
        result = self.v.validate("Show their earnings", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], VERIFIED_RESULT, result["issues_found"])

    # ── Test 10: Simple query with no specific filters ─────────────────────────
    def test_10_no_filters_simple_count(self):
        """Simple count query with no entity/region context → VERIFIED_RESULT (no checks run)."""
        sql = "SELECT COUNT(*) AS total FROM users LIMIT 1"
        ctx = {}  # No filters at all
        rows = [{"total": 12450}]
        result = self.v.validate("How many users are there?", sql, ctx, _exec(rows))
        # No filters to check → nothing failed
        self.assertIn(result["result_confidence"], [VERIFIED_RESULT, UNABLE_TO_VERIFY])
        self.assertEqual(result["issues_found"], [])

    # ── Test 11: Status filter validation ─────────────────────────────────────
    def test_11_status_filter_missing(self):
        """User asked for approved distributors but SQL has no status filter → SUSPICIOUS_RESULT."""
        sql = "SELECT * FROM users WHERE user_role = 4 AND state_id = 29 LIMIT 100"
        ctx = {"entity": "distributor", "role_id": 4, "region": "Karnataka", "status_filter": "approved"}
        rows = [{"id": 1, "status": "pending"}]  # rows returned but status wrong
        result = self.v.validate("Show approved Karnataka distributors", sql, ctx, _exec(rows))
        self.assertEqual(result["result_confidence"], SUSPICIOUS_RESULT)
        self.assertTrue(any("status" in issue.lower() for issue in result["issues_found"]))

    # ── Test 12: Validator is non-blocking on exception ────────────────────────
    def test_12_graceful_fallback_on_internal_error(self):
        """If validation itself raises an exception, result is UNABLE_TO_VERIFY (non-blocking)."""
        # Pass a broken context that will cause an AttributeError in _run_validation
        result = self.v.validate(None, None, None, None)
        self.assertEqual(result["result_confidence"], UNABLE_TO_VERIFY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
