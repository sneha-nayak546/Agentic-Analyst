from app.database.read_executor import execute_read_query
def print_cols(table):
    res = execute_read_query(f'SHOW COLUMNS FROM {table};')
    if res["success"]:
        print(f"--- {table} ---")
        for row in res["data"]:
            print(row['Field'])
print_cols('retailer_distributor_mappings')
print_cols('users')
print_cols('wallet_transaction')
