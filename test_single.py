from app.database.read_executor import execute_read_query

sql = """
SELECT si.sku_code, si.sku_description, si.uom, COUNT(si.id) AS scanned_boxes_count 
FROM sku_inventories AS si 
WHERE si.retailer_scanned_at IS NOT NULL AND si.status_retailer_id IS NOT NULL 
  AND si.retailer_scanned_at >= '2026-08-01 00:00:00' 
GROUP BY si.sku_code, si.sku_description, si.uom;
"""

print("Executing SQL:")
res = execute_read_query(sql)
print("Result:", res)
