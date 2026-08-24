import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database.config import get_master_key, encrypt_payload, get_db_credentials, get_db_engine
from sqlalchemy import text

def secure_environment():
    print("==================================================")
    print(" 🛡️  AES-256 Credentials Encryption Setup")
    print("==================================================")

    master_key_path = PROJECT_ROOT / ".master.key"
    env_path = PROJECT_ROOT / ".env"

    # Step 1: Ensure Master Secret Key exists
    master_key = get_master_key()
    if not master_key:
        print("[+] Generating new Master Secret Key...")
        new_key = Fernet.generate_key().decode("utf-8")
        with open(master_key_path, "w", encoding="utf-8") as f:
            f.write(new_key + "\n")
        master_key = new_key
        print(f"[OK] Saved Master Secret Key to: {master_key_path.name}")
    else:
        print(f"[OK] Master Secret Key detected.")

    # Step 2: Read plain text environment credentials
    load_dotenv(env_path, override=True)

    db_host = os.getenv("DB_HOST", "64.227.153.110")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "jghMasterDB")
    db_user = os.getenv("DB_USER", "readonly")
    db_password = os.getenv("DB_PASSWORD", "DA@simpel2026")

    print(f"\n[+] Raw credentials captured:")
    print(f"    Host: {db_host}")
    print(f"    Port: {db_port}")
    print(f"    User: {db_user}")
    print(f"    Name: {db_name}")

    payload = {
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password
    }

    # Step 3: Encrypt credentials payload
    print("\n[+] Encrypting database credentials using AES-256 (Fernet)...")
    encrypted_ciphertext = encrypt_payload(payload, master_key)

    # Step 4: Overwrite .env with encrypted ciphertext only
    env_content = f"""# Encrypted Database Configuration (AES-256 Fernet)
# Master Secret Key is stored in .master.key or MASTER_SECRET_KEY env var
ENCRYPTED_DB_CONFIG={encrypted_ciphertext}
"""

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("[OK] .env updated with encrypted ciphertext payload.")

    # Step 5: Verification & Decryption Test
    print("\n[+] Verifying in-memory decryption & MySQL connection...")
    import app.database.config as db_config_module
    db_config_module._cached_credentials = None # Reset cache
    os.environ["ENCRYPTED_DB_CONFIG"] = encrypted_ciphertext

    creds = get_db_credentials()
    print(f"[OK] Decrypted credentials successfully in RAM:")
    print(f"    Decrypted Host: {creds['host']}")
    print(f"    Decrypted User: {creds['user']}")
    print(f"    Decrypted Database: {creds['name']}")

    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1;")).fetchone()
            if res and res[0] == 1:
                print("\n[SUCCESS] Connected cleanly to MySQL database using AES-256 decrypted credentials & TLS/SSL!")
    except Exception as e:
        print(f"\n[ERROR] Connection test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    secure_environment()
