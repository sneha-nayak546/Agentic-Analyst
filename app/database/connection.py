import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Load .env file
load_dotenv()

# Read environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print("===================================")
print(" MySQL Connection Test")
print("===================================")
print(f"Host      : {DB_HOST}")
print(f"Port      : {DB_PORT}")
print(f"Username  : {DB_USER}")
print("===================================\n")

# Check if any required value is missing
if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD]):
    print("❌ Missing values in .env file.")
    exit()

# Create connection URL WITHOUT database name
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
)

try:
    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:

        print("✅ Connected Successfully to MySQL Server!\n")

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
    print("\n❌ Connection Failed!\n")
    print(type(e).__name__)
    print(e)