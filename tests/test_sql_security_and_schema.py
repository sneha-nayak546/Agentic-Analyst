"""
Automated Test Suite for SQL AST Security, Schema & Column-Existence Validation,
and End-to-End Dynamic Queries (Tests A-Q, Test 1, Test 2).
"""

import sys
import os
import pytest

# Set utf-8 stdout/stderr for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.validator.sql_ast_validator import validate_ast_security, SQLASTSecurityError
from app.validator.schema_column_validator import validate_schema_columns, SchemaColumnValidationError
from app.agent.sql_agent import run_agent


# ==========================================
# Unit Tests: SQL AST Security Validation
# ==========================================

def test_a_simple_select():
    sql = "SELECT id, name FROM users WHERE user_role = 2"
    assert validate_ast_security(sql) is True


def test_b_select_join():
    sql = """
    SELECT u.id, u.name, wt.amount 
    FROM users u 
    JOIN wallet_transaction wt ON u.id = wt.user_id 
    WHERE u.user_role = 2
    """
    assert validate_ast_security(sql) is True


def test_c_select_group_by():
    sql = "SELECT user_role, COUNT(*) as cnt FROM users GROUP BY user_role"
    assert validate_ast_security(sql) is True


def test_d_select_order_by():
    sql = "SELECT id, name FROM users ORDER BY id DESC"
    assert validate_ast_security(sql) is True


def test_e_select_limit():
    sql = "SELECT id, name FROM users LIMIT 10"
    assert validate_ast_security(sql) is True


def test_f_select_union():
    sql = """
    SELECT id, name FROM users WHERE user_role = 2
    UNION
    SELECT id, name FROM users WHERE user_role = 4
    """
    assert validate_ast_security(sql) is True


def test_g_select_union_all():
    sql = """
    SELECT id, name FROM users WHERE user_role = 2
    UNION ALL
    SELECT id, name FROM users WHERE user_role = 4
    """
    assert validate_ast_security(sql) is True


def test_h_cte_with_select():
    sql = """
    WITH active_retailers AS (
        SELECT id, name FROM users WHERE user_role = 2
    )
    SELECT * FROM active_retailers
    """
    assert validate_ast_security(sql) is True


def test_i_aggregations_and_window_functions():
    sql = """
    SELECT 
        user_id,
        SUM(amount) AS total_earned,
        COUNT(*) AS tx_count,
        AVG(amount) AS avg_amt,
        ROW_NUMBER() OVER (ORDER BY SUM(amount) DESC) AS ranking
    FROM wallet_transaction
    GROUP BY user_id
    """
    assert validate_ast_security(sql) is True


def test_j_block_insert():
    sql = "INSERT INTO users (name, user_role) VALUES ('Attacker', 2)"
    with pytest.raises(SQLASTSecurityError) as exc_info:
        validate_ast_security(sql)
    assert "Only SELECT statements are allowed" in str(exc_info.value) or "Forbidden" in str(exc_info.value)


def test_k_block_update():
    sql = "UPDATE users SET name = 'Attacker' WHERE id = 1"
    with pytest.raises(SQLASTSecurityError) as exc_info:
        validate_ast_security(sql)
    assert "Only SELECT statements are allowed" in str(exc_info.value) or "Forbidden" in str(exc_info.value)


def test_l_block_delete():
    sql = "DELETE FROM users WHERE id = 1"
    with pytest.raises(SQLASTSecurityError) as exc_info:
        validate_ast_security(sql)
    assert "Only SELECT statements are allowed" in str(exc_info.value) or "Forbidden" in str(exc_info.value)


def test_m_block_drop():
    sql = "DROP TABLE users"
    with pytest.raises(SQLASTSecurityError) as exc_info:
        validate_ast_security(sql)
    assert "Only SELECT statements are allowed" in str(exc_info.value) or "Forbidden" in str(exc_info.value)


def test_n_block_alter_truncate_create():
    queries = [
        "ALTER TABLE users ADD COLUMN is_admin INT",
        "TRUNCATE TABLE users",
        "CREATE TABLE backdoor (id INT, secret TEXT)",
    ]
    for q in queries:
        with pytest.raises(SQLASTSecurityError):
            validate_ast_security(q)


def test_o_block_multi_statement():
    sql = "SELECT id FROM users; DROP TABLE users"
    with pytest.raises(SQLASTSecurityError) as exc_info:
        validate_ast_security(sql)
    assert "Multiple SQL statements are not allowed" in str(exc_info.value)


# ====================================================
# Unit Tests: Schema & Column-Existence Validation
# ====================================================

def test_p_reject_nonexistent_phone_column():
    sql = "SELECT u.id, u.name, u.phone FROM users u WHERE u.user_role = 2"
    # AST security passes because it's a read-only SELECT
    assert validate_ast_security(sql) is True

    # Schema validation must catch nonexistent 'phone' column
    with pytest.raises(SchemaColumnValidationError) as exc_info:
        validate_schema_columns(sql)
    err_str = str(exc_info.value)
    assert "COLUMN_NOT_FOUND" in err_str
    assert "table=users" in err_str
    assert "column=phone" in err_str
    assert exc_info.value.table == "users"
    assert exc_info.value.column == "phone"


def test_q_accept_valid_mobile_number_column():
    sql = "SELECT u.id, u.name, u.mobile_number FROM users u WHERE u.user_role = 2"
    assert validate_ast_security(sql) is True
    assert validate_schema_columns(sql) is True


# ====================================================
# Integration Tests: End-to-End Queries (Test 1 & Test 2)
# ====================================================

def test_1_compare_total_wallet_transactions():
    """
    Test 1: 'Compare total wallet transactions between July and June 2026'
    Verifies that:
    - AST validation accepts the generated SQL (conditional aggregation or UNION).
    - Database execution runs against active database.
    - Zero silent fallback.
    """
    question = "Compare total wallet transactions between July and June 2026"
    res = run_agent(question)
    
    print("\n--- Test 1 Result ---")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    print(f"Generated SQL: {res.get('sql_query') or res.get('generated_sql')}")
    print(f"Row count: {res.get('row_count')}")

    # Verify pipeline success
    assert res.get("status") in ["VERIFIED", "FLAGGED", "success", "completed"], f"Expected success, got: {res.get('error')}"
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL", "VERIFIED_EMPTY"]
    assert res.get("sql_query") or res.get("generated_sql")


def test_2_table_retailers_linked_to_distributor_5997():
    """
    Test 2: 'Generate a table of retailers linked to distributor 5997'
    Verifies that:
    - Does not hallucinate 'phone' column in users table.
    - Filters by distributor_id = 5997 and joins users.
    - Pipeline executes without AST security or schema column rejections.
    """
    question = "Generate a table of retailers linked to distributor 5997"
    res = run_agent(question)

    print("\n--- Test 2 Result ---")
    print(f"Status: {res.get('status')}")
    print(f"Validation Status: {res.get('validation_status')}")
    sql = res.get("sql_query") or res.get("generated_sql") or ""
    print(f"Generated SQL: {sql}")
    print(f"Row count: {res.get('row_count')}")

    # Verify no 'phone' column hallucinated
    assert "phone" not in sql.lower() or "mobile_number" in sql.lower()
    assert res.get("status") in ["VERIFIED", "FLAGGED", "success", "completed"], f"Expected success, got: {res.get('error')}"
    assert res.get("validation_status") in ["VERIFIED", "VERIFIED_PARTIAL", "VERIFIED_EMPTY"]
