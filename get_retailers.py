from app.database.read_executor import execute_read_query

query = """
SELECT 
    u.id AS retailer_id, 
    u.name AS retailer_name, 
    u.mobile_number AS mobile_number, 
    COALESCE(SUM(wt.amount), 0) AS total_earnings
FROM retailer_distributor_mappings rdm
JOIN users u ON rdm.retailer_id = u.id
LEFT JOIN wallet_transaction wt ON u.id = wt.user_id 
    AND wt.transaction_type = 1 
    AND MONTH(wt.created_at) = MONTH(CURRENT_DATE())
    AND YEAR(wt.created_at) = YEAR(CURRENT_DATE())
WHERE rdm.distributor_id = 5997
GROUP BY u.id, u.name, u.mobile_number;
"""

res = execute_read_query(query)
if res["success"]:
    data = res["data"]
    if not data:
        print("No retailers found for distributor 5997.")
    else:
        print("| Retailer ID | Retailer Name | Mobile Number | Total Earnings (Current Month) |")
        print("|---|---|---|---|")
        for row in data:
            print(f"| {row.get('retailer_id', '')} | {row.get('retailer_name', '')} | {row.get('mobile_number', '')} | {row.get('total_earnings', 0)} |")
else:
    print("Error:", res["error"])
