from app.database.read_executor import execute_read_query

tables_to_check = ['user_types', 'user_type', 'roles', 'role', 'tbl_user_types', 'tbl_roles', 'mst_user_type', 'master_user_types']
for tbl in tables_to_check:
    res = execute_read_query(f"SELECT * FROM `{tbl}` LIMIT 20;")
    if res.get('success'):
        print(f"Table {tbl} exists! Data:")
        for r in res.get('data', []):
            print(r)

res = execute_read_query("SHOW TABLES LIKE '%type%';")
print("Tables with 'type':", res.get('data'))
res = execute_read_query("SHOW TABLES LIKE '%role%';")
print("Tables with 'role':", res.get('data'))
res = execute_read_query("SHOW TABLES LIKE '%user%';")
print("Tables with 'user':", res.get('data'))
