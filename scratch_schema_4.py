from app.database.read_executor import execute_read_query
res = execute_read_query('SELECT DISTINCT transaction_type FROM wallet_transaction;')
print(res)
