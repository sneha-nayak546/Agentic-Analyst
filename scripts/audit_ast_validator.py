import sys
from pathlib import Path
import json

# Fix encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.validator.sql_ast_validator import validate_sql, SQLValidationError

def run_ast_audit():
    print("=" * 60)
    print(" AST VALIDATION AUDIT")
    print("=" * 60)

    test_cases = [
        # 1. Valid Read Query
        {
            "name": "Simple valid SELECT",
            "sql": "SELECT id, created_at FROM users WHERE id = 1;",
            "expect_pass": True
        },
        # 2. Block WRITE operations
        {
            "name": "Block DELETE",
            "sql": "DELETE FROM users WHERE id = 1;",
            "expect_pass": False
        },
        {
            "name": "Block DROP",
            "sql": "DROP TABLE users;",
            "expect_pass": False
        },
        {
            "name": "Block UPDATE",
            "sql": "UPDATE users SET role = 1 WHERE id = 1;",
            "expect_pass": False
        },
        {
            "name": "Block INSERT",
            "sql": "INSERT INTO users (id) VALUES (1);",
            "expect_pass": False
        },
        # 3. Prevent multiple statements
        {
            "name": "Block multi-statement (SQL injection)",
            "sql": "SELECT * FROM users; DROP TABLE wallet_transaction;",
            "expect_pass": False
        },
        # 4. Sensitive Columns
        {
            "name": "Block password retrieval",
            "sql": "SELECT id, password FROM users;",
            "expect_pass": False
        },
        {
            "name": "Block auth token retrieval",
            "sql": "SELECT id, auth_token FROM users;",
            "expect_pass": False
        },
        # 5. Unknown Tables
        {
            "name": "Block unknown table",
            "sql": "SELECT * FROM super_secret_admin_table;",
            "expect_pass": False
        }
    ]

    passed_checks = 0
    for case in test_cases:
        print(f"\n[Testing] {case['name']}")
        print(f"Query: {case['sql']}")
        try:
            # We pass a fake allowed_tables so it doesn't need DB access for this test
            # except for the unknown table test
            if case['name'] == "Block unknown table":
                validate_sql(case['sql'], allowed_tables=["users", "wallet_transaction"])
            elif "password" in case['sql'] or "auth_token" in case['sql']:
                # The validator doesn't need schema for sensitive column checks
                validate_sql(case['sql'], allowed_tables=["users", "wallet_transaction"])
            else:
                validate_sql(case['sql'], allowed_tables=["users", "wallet_transaction"])
            
            # If it didn't throw an exception, it passed the validator
            if case['expect_pass']:
                print("✅ Passed (Allowed successfully)")
                passed_checks += 1
            else:
                print("❌ Failed (Should have been blocked!)")
        except SQLValidationError as e:
            if not case['expect_pass']:
                print(f"✅ Passed (Blocked successfully: {e})")
                passed_checks += 1
            else:
                print(f"❌ Failed (Should have been allowed, but got: {e})")
        except Exception as e:
            print(f"❌ Failed with unknown error: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed_checks}/{len(test_cases)} tests passed.")

if __name__ == "__main__":
    run_ast_audit()
