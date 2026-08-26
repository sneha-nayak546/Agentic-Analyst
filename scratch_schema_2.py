from app.database.read_executor import execute_read_query
print(execute_read_query('SHOW COLUMNS FROM retailer_distributor_mappings;'))
print(execute_read_query('SHOW COLUMNS FROM users;'))
print(execute_read_query('SHOW TABLES LIKE "%wallet%";'))
print(execute_read_query('SHOW TABLES LIKE "%earning%";'))
