from app.database.read_executor import execute_read_query
import json

print("=== DISTRIBUTORS (user_role=4) STATE_ID COUNTS ===")
res1 = execute_read_query("SELECT state_id, COUNT(*) as cnt FROM users WHERE user_role = 4 GROUP BY state_id ORDER BY cnt DESC")
print(json.dumps(res1, indent=2))

print("\n=== DISTRIBUTORS SAMPLE ===")
res2 = execute_read_query("SELECT id, name, user_role, state_id, city, district, address FROM users WHERE user_role = 4 LIMIT 15")
print(json.dumps(res2, indent=2))

print("\n=== ANY USERS WITH STATE/CITY/DISTRICT/ADDRESS IN KARNATAKA ===")
res3 = execute_read_query("SELECT id, name, user_role, state_id, city, district, address FROM users WHERE city LIKE '%bangal%' OR city LIKE '%bengal%' OR district LIKE '%bangal%' OR district LIKE '%karnat%' OR address LIKE '%karnat%' LIMIT 20")
print(json.dumps(res3, indent=2))

print("\n=== DISTINCT CITIES FOR DISTRIBUTORS ===")
res4 = execute_read_query("SELECT city, COUNT(*) as cnt FROM users WHERE user_role = 4 GROUP BY city ORDER BY cnt DESC LIMIT 20")
print(json.dumps(res4, indent=2))

print("\n=== MECHANIC_DETAILS REGION / AREA OFFICE ===")
res5 = execute_read_query("SELECT region, area_office_name, COUNT(*) as cnt FROM mechanic_details GROUP BY region, area_office_name ORDER BY cnt DESC LIMIT 20")
print(json.dumps(res5, indent=2))
