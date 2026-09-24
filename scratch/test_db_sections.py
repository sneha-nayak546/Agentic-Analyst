import sys
from app.database.read_executor import execute_read_query

def main():
    print("State columns:")
    r = execute_read_query("DESCRIBE state;")
    for row in r.get("data", []):
        print(row.get("Field"), row.get("Type"))

    r2 = execute_read_query("SELECT id, name FROM state LIMIT 5;")
    print("State rows:", r2.get("data"))

    print("\nUser roles count:")
    r3 = execute_read_query("SELECT user_role, COUNT(*) as cnt FROM users GROUP BY user_role;")
    print("Roles:", r3.get("data"))

if __name__ == "__main__":
    main()
