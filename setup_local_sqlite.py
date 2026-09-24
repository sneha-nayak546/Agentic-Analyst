import sqlite3
import pandas as pd
import os

DB_PATH = "database.db"

def setup_local_database():
    print(f"Setting up local fallback SQLite database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Table: users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        mobile_number TEXT,
        email TEXT,
        user_role INTEGER,
        state_id INTEGER,
        city TEXT,
        district TEXT,
        address TEXT,
        wallet_balance REAL DEFAULT 0.0,
        status TEXT DEFAULT 'approved',
        created_at TEXT DEFAULT '2026-01-01 00:00:00',
        updated_at TEXT DEFAULT '2026-01-01 00:00:00'
    );
    """)

    # 2. Table: retailer_distributor_mappings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS retailer_distributor_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        retailer_id INTEGER,
        distributor_id INTEGER,
        created_at TEXT DEFAULT '2026-01-01 00:00:00'
    );
    """)

    # Insert sample users
    users_data = [
        (5997, 'Sri Balaji Distributors', '9876543210', 'balaji@distrib.com', 4, 11, 'Bengaluru', 'Bengaluru Urban', 'MG Road', 45000.0, 'approved', '2025-01-01 10:00:00'),
        (6016, 'Devyani And Company', '9096500543', 'devyani@distrib.com', 4, 14, 'Satara', 'Satara', 'Main Road', 32000.0, 'approved', '2025-01-10 10:00:00'),
        (5903, 'Pottekat Baiju Distributor', '9847135299', 'pottekat@distrib.com', 4, 12, 'Kochi', 'Ernakulam', 'Marine Drive', 28000.0, 'approved', '2025-01-15 10:00:00'),
        (50225, 'Lakshmi Enterprises Retailer', '9876543211', 'lakshmi@retail.com', 2, 11, 'Bengaluru', 'Bengaluru Urban', 'Indiranagar', 12500.0, 'approved', '2025-02-01 11:00:00'),
        (50284, 'Shree Ganesh Traders Retailer', '9876543212', 'ganesh@retail.com', 2, 11, 'Mysuru', 'Mysuru', 'Sayyaji Rao Rd', 8400.0, 'approved', '2025-02-05 11:00:00'),
        (50751, 'Kaveri Stores Retailer', '9876543213', 'kaveri@retail.com', 2, 11, 'Hubli', 'Dharwad', 'Station Road', 15200.0, 'approved', '2025-02-10 11:00:00'),
        (52699, 'Saraswati Agencies Retailer', '9876543214', 'saraswati@retail.com', 2, 12, 'Kochi', 'Ernakulam', 'Banerji Rd', 6100.0, 'approved', '2025-02-15 11:00:00'),
        (62977, 'Balaji Retail Store', '9876543215', 'balaji@retail.com', 2, 14, 'Pune', 'Pune', 'FC Road', 9200.0, 'approved', '2025-03-01 11:00:00'),
        (63852, 'Mahalakshmi Retail Store', '9876543216', 'maha@retail.com', 2, 14, 'Mumbai', 'Mumbai', 'Dadar West', 18400.0, 'approved', '2025-03-10 11:00:00'),
        (77802, 'Venkateshwara Stores Retailer', '9876543217', 'venkat@retail.com', 2, 11, 'Bengaluru', 'Bengaluru Urban', 'Jayanagar', 14300.0, 'approved', '2025-03-15 11:00:00'),
        (56229, 'Royal Retailers', '9876543218', 'royal@retail.com', 2, 11, 'Bengaluru', 'Bengaluru Urban', 'Whitefield', 5500.0, 'approved', '2025-03-20 11:00:00'),
        (64945, 'Apex Wholesalers', '9876543219', 'apex@whole.com', 5, 11, 'Bengaluru', 'Bengaluru Urban', 'Peenya', 50000.0, 'approved', '2025-01-20 10:00:00')
    ]

    cur.executemany("""
    INSERT OR REPLACE INTO users (id, name, mobile_number, email, user_role, state_id, city, district, address, wallet_balance, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users_data)

    # Insert retailer_distributor_mappings
    rdm_data = [
        (50225, 5997),
        (50284, 5997),
        (50751, 5997),
        (77802, 5997),
        (56229, 5997),
        (52699, 5903),
        (62977, 6016),
        (63852, 6016)
    ]
    cur.executemany("""
    INSERT OR IGNORE INTO retailer_distributor_mappings (retailer_id, distributor_id)
    VALUES (?, ?)
    """, rdm_data)

    # 3. Load Wallet_Transaction_Dump_Data.csv if present
    if os.path.exists("Wallet_Transaction_Dump_Data.csv"):
        df_wt = pd.read_csv("Wallet_Transaction_Dump_Data.csv")
        df_wt.to_sql("wallet_transaction", conn, if_exists="replace", index=False)
        print(f"Loaded {len(df_wt)} rows into wallet_transaction.")

    # 4. Load Sku_Inventeries_Dump_data.csv if present
    if os.path.exists("Sku_Inventeries_Dump_data.csv"):
        df_sku = pd.read_csv("Sku_Inventeries_Dump_data.csv")
        df_sku.to_sql("sku_inventories", conn, if_exists="replace", index=False)
        print(f"Loaded {len(df_sku)} rows into sku_inventories.")

    conn.commit()
    conn.close()
    print("Local fallback SQLite database setup complete.")

if __name__ == "__main__":
    setup_local_database()
