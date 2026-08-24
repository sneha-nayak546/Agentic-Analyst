
from app.database.read_executor import execute_read_query
print(execute_read_query('SHOW COLUMNS FROM users;'))
print(execute_read_query('SHOW TABLES LIKE "%distributor%";'))
print(execute_read_query('SHOW TABLES LIKE "%retailer%";'))
print(execute_read_query('SHOW TABLES LIKE "%map%";'))

