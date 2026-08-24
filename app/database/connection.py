import sys
from sqlalchemy import text
from app.database.config import get_db_credentials, get_db_engine

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

def test_connection():
    creds = get_db_credentials()
    print("===================================")
    print(" MySQL Connection Test (AES-256 Secured)")
    print("===================================")
    print(f"Host      : {creds['host']}")
    print(f"Port      : {creds['port']}")
    print(f"Username  : {creds['user']}")
    print("===================================\n")

    if not all([creds['host'], creds['port'], creds['user'], creds['password']]):
        print("[X] Missing values in encrypted database configuration.")
        return

    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            print("[OK] Connected Successfully to MySQL Server (AES-256 Decrypted RAM Credentials & TLS/SSL Wire Encryption)!\n")
            print("Attempting to list available databases...\n")
            result = connection.execute(text("SHOW DATABASES;"))
            print("Accessible Databases")
            print("---------------------")
            found = False
            for db in result:
                found = True
                print(f"• {db[0]}")
            if not found:
                print("No databases found.")
    except Exception as e:
        print("\n[X] Connection Failed!\n")
        print(type(e).__name__)
        print(e)

if __name__ == "__main__":
    test_connection()