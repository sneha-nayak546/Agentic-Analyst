import sqlite3

def get_tables(db_name):
    print(f"--- {db_name} ---")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for (table,) in tables:
        print(f"Table: {table}")
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col}")
    conn.close()

get_tables('database.db')
get_tables('jgh_enterprise_test.db')
