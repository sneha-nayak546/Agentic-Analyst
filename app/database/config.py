import os
import json
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Project root resolution (parent of app directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env file from project root or current working directory
dotenv_path = PROJECT_ROOT / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

_cached_credentials = None

def get_master_key() -> str:
    """
    Retrieves the Master Secret Key from environment variables or .master.key file.
    """
    env_key = os.getenv("MASTER_SECRET_KEY")
    if env_key:
        return env_key.strip()
    
    key_file = PROJECT_ROOT / ".master.key"
    if key_file.exists():
        with open(key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    
    # Check current working directory as fallback
    cwd_key_file = Path(".master.key")
    if cwd_key_file.exists():
        with open(cwd_key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
            
    return None

def decrypt_payload(encrypted_str: str, key: str) -> dict:
    """
    Decrypts an AES-256 Fernet encrypted payload string back into a credential dictionary.
    """
    try:
        fernet = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
        decrypted_bytes = fernet.decrypt(encrypted_str.encode("utf-8"))
        return json.loads(decrypted_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Failed to decrypt database configuration: {str(e)}")

def encrypt_payload(data_dict: dict, key: str) -> str:
    """
    Encrypts a credential dictionary into an AES-256 Fernet ciphertext string.
    """
    json_bytes = json.dumps(data_dict).encode("utf-8")
    fernet = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    return fernet.encrypt(json_bytes).decode("utf-8")

def get_db_credentials() -> dict:
    """
    Retrieves decrypted database credentials from RAM.
    Returns dict containing: host, port, name, user, password.
    """
    global _cached_credentials
    if _cached_credentials is not None:
        return _cached_credentials

    encrypted_config = os.getenv("ENCRYPTED_DB_CONFIG")
    
    if encrypted_config:
        master_key = get_master_key()
        if not master_key:
            raise RuntimeError(
                "ENCRYPTED_DB_CONFIG is present in .env, but Master Secret Key was not found! "
                "Ensure MASTER_SECRET_KEY is set in environment or stored in .master.key"
            )
        config = decrypt_payload(encrypted_config, master_key)
        creds = {
            "host": config.get("DB_HOST", "localhost"),
            "port": str(config.get("DB_PORT", "3306")),
            "name": config.get("DB_NAME", ""),
            "user": config.get("DB_USER", ""),
            "password": config.get("DB_PASSWORD", ""),
        }
    else:
        # Fallback to plain-text environment variables
        creds = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "3306"),
            "name": os.getenv("DB_NAME", ""),
            "user": os.getenv("DB_USER", ""),
            "password": os.getenv("DB_PASSWORD", ""),
        }

    # Allow explicit environment variables to override defaults
    if os.getenv("DB_HOST"):
        creds["host"] = os.getenv("DB_HOST").strip()
    if os.getenv("DB_PORT"):
        creds["port"] = os.getenv("DB_PORT").strip()
    if os.getenv("DB_NAME"):
        creds["name"] = os.getenv("DB_NAME").strip()
    if os.getenv("DB_USER"):
        creds["user"] = os.getenv("DB_USER").strip()
    if os.getenv("DB_PASSWORD"):
        creds["password"] = os.getenv("DB_PASSWORD").strip()

    _cached_credentials = creds
    return _cached_credentials

def get_db_url() -> URL:
    """
    Constructs a SQLAlchemy URL object from decrypted database credentials.
    """
    creds = get_db_credentials()
    return URL.create(
        drivername="mysql+pymysql",
        username=creds["user"],
        password=creds["password"],
        host=creds["host"],
        port=int(creds["port"]) if creds["port"] else 3306,
        database=creds["name"],
    )

def get_db_engine(**kwargs):
    """
    Creates a SQLAlchemy Engine configured with optional TLS/SSL wire encryption.
    """
    url = get_db_url()
    connect_args = kwargs.pop("connect_args", {})
    if os.getenv("DB_SSL", "").lower() in ("true", "1", "yes"):
        if "ssl" not in connect_args:
            connect_args["ssl"] = {}
    if "connect_timeout" not in connect_args:
        connect_args["connect_timeout"] = int(os.getenv("DB_CONNECT_TIMEOUT", "3"))
    
    default_kwargs = {
        "connect_args": connect_args,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }
    default_kwargs.update(kwargs)
    return create_engine(url, **default_kwargs)
