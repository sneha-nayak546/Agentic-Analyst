import sys
import json
sys.path.insert(0, r"c:\Users\nayak_o7hopi6\Desktop\Agent")

from app.prompt.prompt_builder import build_sql_prompt
from app.knowledge.knowledge_graph import get_knowledge_graph

def run_sku_tests():
    print("=" * 80)
    print("RUNNING SKU INVENTORY & DUAL-ROLE SCANNING TEST CASES")
    print("=" * 80)

    kg = get_knowledge_graph(reload=True)

    # -------------------------------------------------------------
    # CASE A: Retailer Scanned Boxes for July 2026
    # -------------------------------------------------------------
    q_a = "Show scanned boxes count by SKU code with grid type and UOM for retailers for July 2026"
    print(f"\n[TEST CASE A] Prompt: '{q_a}'")

    res_a = kg.resolve_business_query(q_a)
    print(f"  - Detected Tables: {res_a['detected_tables']}")
    print(f"  - Detected Joins: {res_a['detected_joins']}")
    print(f"  - Date Range: {res_a['date_range']}")

    plan_a = {
        "intent": q_a,
        "primary_entity": "sku_inventories",
        "target_measures": ["COUNT(si.id) AS scanned_boxes_count"],
        "dimensions": ["si.sku_code", "si.sku_description", "map.gride_type", "map.uom", "map.box_calculation_uom"],
        "time_filter": "retailer_scanned_at >= '2026-07-01 00:00:00' AND retailer_scanned_at < '2026-08-01 00:00:00'",
        "table_columns": {
            "sku_inventories": ["id", "sku_code", "sku_description", "retailer_scanned_at", "status_retailer_id"],
            "sku_qr_points_map": ["id", "sku_code", "gride_type", "uom", "box_calculation_uom"]
        },
        "relationships_required": ["JOIN sku_qr_points_map map ON si.sku_code = map.sku_code"]
    }

    prompt_a = build_sql_prompt(json.dumps(plan_a))

    assert "sku_inventories" in res_a["detected_tables"]
    assert any("sku_code = sku_qr_points_map.sku_code" in j for j in res_a["detected_joins"]) or any("sku_code = sku_qr_points_map.sku_code" in j for j in plan_a["relationships_required"])
    print("  - [PASS] Case A Table detection and join path verified.")

    # -------------------------------------------------------------
    # CASE B: Wholesaler Scanned Items by Warehouse
    # -------------------------------------------------------------
    q_b = "Show top 5 warehouses by invoiced quantity for wholesaler scanned items"
    print(f"\n[TEST CASE B] Prompt: '{q_b}'")

    res_b = kg.resolve_business_query(q_b)
    print(f"  - Detected Tables: {res_b['detected_tables']}")
    print(f"  - Detected Joins: {res_b['detected_joins']}")

    plan_b = {
        "intent": q_b,
        "primary_entity": "sku_inventories",
        "target_measures": ["SUM(si.invoiced_quantity) AS total_invoiced_quantity"],
        "dimensions": ["si.warehouse"],
        "table_columns": {
            "sku_inventories": ["id", "warehouse", "invoiced_quantity", "wholesaler_scanned_at", "status_wholeseller_id"]
        }
    }

    prompt_b = build_sql_prompt(json.dumps(plan_b))

    assert "sku_inventories" in res_b["detected_tables"]
    print("  - [PASS] Case B Table detection verified.")

    print("\n" + "=" * 80)
    print("ALL SKU TEST CASES PASSED VERIFICATION!")
    print("=" * 80)

if __name__ == "__main__":
    run_sku_tests()
