"""
Comprehensive Architectural Grounding, SQL Validation, Database Result Handling,
and Response Integrity Test Suite (Sections 17, 18, 19).
"""

import os
import sys
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.business_requirement import BusinessRequirement
from app.agent.execution_plan import ExecutionPlan
from app.agent.verified_result import VerifiedResult
from app.agent.response_generator import response_generator
from app.validator.sql_ast_validator import validate_ast_security, SQLASTSecurityError
from app.validator.schema_column_validator import validate_schema_columns, SchemaColumnValidationError
from app.validator.semantic_sql_validator import evaluate_semantic_sql, validate_semantic_sql, SemanticValidationError
from app.validator.response_accuracy_validator import response_accuracy_validator
from app.agent.sql_agent import run_agent


# ==============================================================================
# SECTION 18: NEGATIVE TESTS
# ==============================================================================

class TestNegativeValidation:
    """
    Verifies that the system deterministically rejects:
    - Box scan questions attempting to use wallet_transaction (METRIC_SOURCE_MISMATCH)
    - Box scan questions attempting to use users.created_at (TEMPORAL_SOURCE_MISMATCH)
    - Non-existent columns like users.phone (COLUMN_NOT_FOUND)
    - Non-SELECT mutations: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
    - Multi-statement SQL
    - Wrong ranking directions (e.g. ASC for highest)
    - Missing GROUP BY or missing LIMIT for top-1 ranking
    """

    def test_reject_box_scans_using_wallet_transactions(self):
        """Reject box scan queries attempting to substitute wallet_transaction table."""
        req = BusinessRequirement(
            original_question="Which distributor has the highest number of box scans this month?",
            intent="ranking",
            entities=["distributor"],
            metric="box_scan_count",
            metrics=["box_scans"],
            metric_source="sku_inventories.id",
            aggregation=["COUNT"],
            periods=["this month"],
            ranking="top 1",
            limit=1
        )
        plan = ExecutionPlan(business_requirement=req, relevant_tables=["wallet_transaction", "users"])
        wrong_sql = (
            "SELECT u.id, COUNT(wt.id) AS box_scans "
            "FROM wallet_transaction wt "
            "JOIN users u ON wt.user_id = u.id "
            "WHERE u.user_role = 4 "
            "GROUP BY u.id ORDER BY box_scans DESC LIMIT 1"
        )
        with pytest.raises(SemanticValidationError) as exc:
            validate_semantic_sql(wrong_sql, plan)
        assert "METRIC_SOURCE_MISMATCH" in str(exc.value)

    def test_reject_box_scans_using_users_created_at(self):
        """Reject box scan queries filtering on users.created_at instead of retailer_scanned_at."""
        req = BusinessRequirement(
            original_question="Which distributor has the highest number of box scans this month?",
            intent="ranking",
            entities=["distributor"],
            metric="box_scan_count",
            metrics=["box_scans"],
            metric_source="sku_inventories.id",
            aggregation=["COUNT"],
            periods=["this month"],
            ranking="top 1",
            limit=1
        )
        plan = ExecutionPlan(business_requirement=req, relevant_tables=["sku_inventories", "users"])
        wrong_sql = (
            "SELECT u.id, COUNT(si.id) AS box_scans "
            "FROM sku_inventories si "
            "JOIN users u ON si.distributer_id = u.id "
            "WHERE u.user_role = 4 AND u.created_at >= '2026-09-01' "
            "GROUP BY u.id ORDER BY box_scans DESC LIMIT 1"
        )
        with pytest.raises(SemanticValidationError) as exc:
            validate_semantic_sql(wrong_sql, plan)
        assert "TEMPORAL_SOURCE_MISMATCH" in str(exc.value)

    def test_reject_nonexistent_phone_column(self):
        """Reject non-existent columns (e.g. users.phone)."""
        sql = "SELECT id, name, phone FROM users WHERE user_role = 2"
        with pytest.raises(SchemaColumnValidationError) as exc:
            validate_schema_columns(sql, allowed_tables=["users"])
        assert "COLUMN_NOT_FOUND" in str(exc.value)
        assert "phone" in str(exc.value)

    def test_reject_non_select_mutations(self):
        """Reject non-read-only SQL statements."""
        forbidden_statements = [
            "INSERT INTO users (name, user_role) VALUES ('Hacker', 1)",
            "UPDATE users SET user_role = 1 WHERE id = 10",
            "DELETE FROM users WHERE id = 5",
            "DROP TABLE users",
            "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)",
            "TRUNCATE TABLE wallet_transaction"
        ]
        for query in forbidden_statements:
            with pytest.raises(SQLASTSecurityError):
                validate_ast_security(query)

    def test_reject_multi_statements(self):
        """Reject chained multi-statement execution."""
        multi_sql = "SELECT * FROM users; DROP TABLE users;"
        with pytest.raises(SQLASTSecurityError):
            validate_ast_security(multi_sql)

    def test_reject_wrong_ranking_direction(self):
        """Reject queries that use ASC when highest/top ranking is requested."""
        req = BusinessRequirement(
            original_question="Which distributor has the highest number of box scans this month?",
            intent="ranking",
            entities=["distributor"],
            metric="box_scan_count",
            metrics=["box_scans"],
            ranking_direction="DESC",
            ranking="top 1",
            limit=1
        )
        plan = ExecutionPlan(business_requirement=req, relevant_tables=["sku_inventories", "users"])
        wrong_sql = (
            "SELECT u.id, COUNT(si.id) AS box_scan_count "
            "FROM sku_inventories si JOIN users u ON si.distributer_id = u.id "
            "WHERE si.retailer_scanned_at >= '2026-09-01' "
            "GROUP BY u.id ORDER BY box_scan_count ASC LIMIT 1"
        )
        with pytest.raises(SemanticValidationError) as exc:
            validate_semantic_sql(wrong_sql, plan)
        assert "RANKING_REQUIREMENT_MISMATCH" in str(exc.value)

    def test_reject_missing_group_by_in_ranking(self):
        """Reject entity ranking queries that fail to include GROUP BY."""
        req = BusinessRequirement(
            original_question="Which distributor has the highest number of box scans this month?",
            intent="ranking",
            entities=["distributor"],
            metric="box_scan_count",
            metrics=["box_scans"],
            ranking_direction="DESC",
            ranking="top 1",
            limit=1
        )
        plan = ExecutionPlan(business_requirement=req, relevant_tables=["sku_inventories", "users"])
        wrong_sql = (
            "SELECT u.id, COUNT(si.id) AS box_scan_count "
            "FROM sku_inventories si JOIN users u ON si.distributer_id = u.id "
            "WHERE si.retailer_scanned_at >= '2026-09-01' "
            "ORDER BY box_scan_count DESC LIMIT 1"
        )
        with pytest.raises(SemanticValidationError) as exc:
            validate_semantic_sql(wrong_sql, plan)
        assert "RANKING_REQUIREMENT_MISMATCH" in str(exc.value)
        assert "GROUP BY" in str(exc.value)

    def test_reject_missing_limit_in_ranking(self):
        """Reject top-1 ranking queries that fail to include LIMIT 1."""
        req = BusinessRequirement(
            original_question="Which distributor has the highest number of box scans this month?",
            intent="ranking",
            entities=["distributor"],
            metric="box_scan_count",
            metrics=["box_scans"],
            ranking_direction="DESC",
            ranking="top 1",
            limit=1
        )
        plan = ExecutionPlan(business_requirement=req, relevant_tables=["sku_inventories", "users"])
        wrong_sql = (
            "SELECT u.id, COUNT(si.id) AS box_scan_count "
            "FROM sku_inventories si JOIN users u ON si.distributer_id = u.id "
            "WHERE si.retailer_scanned_at >= '2026-09-01' "
            "GROUP BY u.id ORDER BY box_scan_count DESC"
        )
        with pytest.raises(SemanticValidationError) as exc:
            validate_semantic_sql(wrong_sql, plan)
        assert "RANKING_REQUIREMENT_MISMATCH" in str(exc.value)
        assert "LIMIT 1" in str(exc.value)


# ==============================================================================
# SECTION 19: RESPONSE INTEGRITY TESTS
# ==============================================================================

class TestResponseIntegrity:
    """
    Verifies that the natural language response:
    - Never inverts row periods (order agnostic: row 0 vs row 1 does not dictate period)
    - Preserves NULL as N/A and never silences NULL to 0
    - Formats box counts as plain numbers and never adds currency symbol (₹)
    - Validates response accuracy against VerifiedResult
    """

    def test_order_agnostic_period_matching_july_first(self):
        """Test response generator correctly attributes periods when July is row 0."""
        vr = VerifiedResult(
            question="Compare total wallet transactions between July and June 2026",
            business_requirement={"entities": ["wallet_transaction"], "metric": "earnings"},
            execution_plan={},
            sql="SELECT ...",
            columns=["period", "total_amount"],
            data=[
                {"period": "July 2026", "total_amount": 7987.50},
                {"period": "June 2026", "total_amount": 5420.00}
            ],
            row_count=2,
            metric="earnings"
        )
        resp = response_generator.generate_from_verified_result(vr)
        assert "July 2026" in resp
        assert "7,987.50" in resp or "7987.5" in resp
        assert "June 2026" in resp
        assert "5,420.00" in resp or "5420" in resp

        # Verify Response Accuracy Validator passes
        val = response_accuracy_validator.validate(
            question=vr.question,
            requirement=vr.business_requirement,
            sql=vr.sql,
            execution_result={"columns": vr.columns, "data": vr.data, "row_count": 2},
            final_response=resp
        )
        assert val["is_valid"] is True

    def test_order_agnostic_period_matching_june_first(self):
        """Test response generator correctly attributes periods when June is row 0."""
        vr = VerifiedResult(
            question="Compare total wallet transactions between July and June 2026",
            business_requirement={"entities": ["wallet_transaction"], "metric": "earnings"},
            execution_plan={},
            sql="SELECT ...",
            columns=["period", "total_amount"],
            data=[
                {"period": "June 2026", "total_amount": 5420.00},
                {"period": "July 2026", "total_amount": 7987.50}
            ],
            row_count=2,
            metric="earnings"
        )
        resp = response_generator.generate_from_verified_result(vr)
        assert "July 2026" in resp
        assert "7,987.50" in resp or "7987.5" in resp
        assert "June 2026" in resp
        assert "5,420.00" in resp or "5420" in resp

        # Verify Response Accuracy Validator passes
        val = response_accuracy_validator.validate(
            question=vr.question,
            requirement=vr.business_requirement,
            sql=vr.sql,
            execution_result={"columns": vr.columns, "data": vr.data, "row_count": 2},
            final_response=resp
        )
        assert val["is_valid"] is True

    def test_null_preservation_not_converted_to_zero(self):
        """Test that NULL database values are preserved as N/A and not coerced to 0."""
        vr = VerifiedResult(
            question="Compare total wallet transactions between July and June 2026",
            business_requirement={"entities": ["wallet_transaction"], "metric": "earnings"},
            execution_plan={},
            sql="SELECT ...",
            columns=["period", "total_amount"],
            data=[
                {"period": "July 2026", "total_amount": 7987.50},
                {"period": "June 2026", "total_amount": None}
            ],
            row_count=2,
            metric="earnings"
        )
        resp = response_generator.generate_from_verified_result(vr)
        assert "July 2026" in resp
        assert "June 2026" in resp
        assert "N/A" in resp
        assert "June 2026: ₹0" not in resp
        assert "June 2026: 0" not in resp

        # Accurate response passes
        val = response_accuracy_validator.validate(
            question=vr.question,
            requirement=vr.business_requirement,
            sql=vr.sql,
            execution_result={"columns": vr.columns, "data": vr.data, "row_count": 2},
            final_response=resp
        )
        assert val["is_valid"] is True

        # Inaccurate response claiming June was 0 must be rejected
        hallucinated_resp = "In July 2026 total was ₹7,987.50, whereas June 2026 was 0."
        fail_val = response_accuracy_validator.validate(
            question=vr.question,
            requirement=vr.business_requirement,
            sql=vr.sql,
            execution_result={"columns": vr.columns, "data": vr.data, "row_count": 2},
            final_response=hallucinated_resp
        )
        assert fail_val["is_valid"] is False
        assert any("CONTRADICTS_DATABASE_RESULT" in cat for cat in fail_val["categories"]) or any("CONTRADICTS_DATABASE_RESULT" in issue for issue in fail_val["issues"])

    def test_no_currency_symbols_on_box_scans(self):
        """Test box scan metrics are never formatted with currency symbols like ₹."""
        vr = VerifiedResult(
            question="Which distributor has the highest number of box scans this month?",
            business_requirement={"entities": ["distributor"], "metric": "box_scan_count"},
            execution_plan={},
            sql="SELECT ...",
            columns=["distributor_name", "box_scan_count"],
            data=[
                {"distributor_name": "Agro Trade Co", "box_scan_count": 64}
            ],
            row_count=1,
            metric="box_scan_count"
        )
        resp = response_generator.generate_from_verified_result(vr)
        assert "₹" not in resp
        assert "64" in resp
        assert "box scans" in resp or "scans" in resp or "boxes" in resp

        # Response Accuracy Validator rejects currency symbols on counts
        wrong_currency_resp = "Agro Trade Co had the highest number of box scans with ₹64."
        val_cur = response_accuracy_validator.validate(
            question=vr.question,
            requirement=vr.business_requirement,
            sql=vr.sql,
            execution_result={"columns": vr.columns, "data": vr.data, "row_count": 1},
            final_response=wrong_currency_resp
        )
        assert val_cur["is_valid"] is False
        assert any("FORMAT_ERROR" in cat for cat in val_cur["categories"]) or any("FORMAT_ERROR" in issue for issue in val_cur["issues"])


# ==============================================================================
# SECTION 17: THE 13 ANALYTICAL BUSINESS QUESTIONS
# ==============================================================================

class TestAnalyticalBusinessQuestions:
    """
    End-to-End Regression Tests for the 13 required business analytical queries.
    """

    def test_q01_show_all_retailers(self):
        """TEST 1: Show all retailers"""
        res = run_agent("Show all retailers")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "users" in sql.lower()
        assert "user_role" in sql.lower()

    def test_q02_table_of_retailers_linked_to_distributor_5997(self):
        """TEST 2: Generate a table of retailers linked to distributor 5997"""
        res = run_agent("Generate a table of retailers linked to distributor 5997")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "5997" in sql
        assert "phone" not in sql.lower()

    def test_q03_total_wallet_amount_july_2026(self):
        """TEST 3: Show total wallet amount for July 2026"""
        res = run_agent("Show total wallet amount for July 2026")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "wallet_transaction" in sql.lower()
        assert "2026-07" in sql or "2026-08" in sql or "MONTH" in sql.upper() or "7" in sql

    def test_q04_compare_wallet_transactions_july_and_june_2026(self):
        """TEST 4: Compare total wallet transactions between July and June 2026"""
        res = run_agent("Compare total wallet transactions between July and June 2026")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "wallet_transaction" in sql.lower()

    def test_q05_top_10_retailers_by_earnings_july_2026(self):
        """TEST 5: Show top 10 retailers by earnings for July 2026"""
        res = run_agent("Show top 10 retailers by earnings for July 2026")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "LIMIT 10" in sql.upper()
        assert "DESC" in sql.upper()
        assert "wallet_transaction" in sql.lower()

    def test_q06_distributor_highest_box_scans_this_month(self):
        """TEST 6: Which distributor has the highest number of box scans this month?"""
        res = run_agent("Which distributor has the highest number of box scans this month?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()
        assert "LIMIT 1" in sql.upper()
        assert "DESC" in sql.upper()

    def test_q07_retailer_under_distributor_highest_box_scans(self):
        """TEST 7: Which retailer under which distributor has scanned the highest number of boxes this month?"""
        res = run_agent("Which retailer under which distributor has scanned the highest number of boxes this month?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()
        assert "LIMIT 1" in sql.upper()
        assert "DESC" in sql.upper()

    def test_q08_state_with_highest_box_scans(self):
        """TEST 8: Which state has the highest number of box scans this month?"""
        res = run_agent("Which state has the highest number of box scans this month?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "state_id" in sql.lower() or "state" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()

    def test_q09_category_with_highest_box_scans(self):
        """TEST 9: Which category has the highest number of box scans this month?"""
        res = run_agent("Which category has the highest number of box scans this month?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "sku_description" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()

    def test_q10_lowest_category_and_lowest_state_box_scans(self):
        """TEST 10: Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?"""
        res = run_agent("Which category has the lowest number of box scans this month, and which state has the lowest number of box scans?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "sku_description" in sql.lower()
        assert "state_id" in sql.lower() or "state" in sql.lower()
        assert "ASC" in sql.upper()

    def test_q11_distributor_with_lowest_box_scans(self):
        """TEST 11: Which distributor has the lowest number of box scans this month?"""
        res = run_agent("Which distributor has the lowest number of box scans this month?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()
        assert "ASC" in sql.upper()
        assert "LIMIT 1" in sql.upper()

    def test_q12_retailer_with_highest_box_scans(self):
        """TEST 12: Which retailer has scanned the highest number of boxes this month?"""
        res = run_agent("Which retailer has scanned the highest number of boxes this month?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()
        assert "LIMIT 1" in sql.upper()
        assert "DESC" in sql.upper()

    def test_q13_category_with_highest_box_scans_july_2026(self):
        """TEST 13: Which category has the highest box scan count in July 2026?"""
        res = run_agent("Which category has the highest box scan count in July 2026?")
        assert res.get("status") in ["VERIFIED", "VERIFIED_EMPTY"]
        sql = res.get("sql_query") or res.get("generated_sql") or ""
        assert "sku_inventories" in sql.lower()
        assert "sku_description" in sql.lower()
        assert "retailer_scanned_at" in sql.lower()
        assert "2026-07" in sql or "2026-08" in sql
        assert "LIMIT 1" in sql.upper()
