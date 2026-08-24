"""
Draft Business Dictionary Generator for JGH Intelligence Engine.
Processes draft_db_profile.json and generates a structured business dictionary template
(knowledge/business_dictionary.json) ready for human labeling.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

def generate_draft_dictionary():
    print("=" * 60)
    print(" 📖 JGH Intelligence Engine - Draft Business Dictionary Generator")
    print("=" * 60)

    draft_profile_path = KNOWLEDGE_DIR / "draft_db_profile.json"
    if not draft_profile_path.exists():
        print(f"[!] Warning: {draft_profile_path.name} not found. Running dictionary template generation with default profile structures...")
        profile_data = {}
    else:
        with open(draft_profile_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

    # 1. User Role Mappings (explicitly for roles 2, 4, 5 and any others found in draft profile)
    user_roles_data = {}
    users_profile = profile_data.get("targeted_columns", {}).get("users.user_role") or \
                    profile_data.get("all_low_cardinality_columns", {}).get("users.user_role", {})

    target_roles = ["2", "4", "5"]
    if users_profile and "distinct_values" in users_profile:
        for item in users_profile["distinct_values"]:
            val_str = str(item["value"])
            if val_str not in target_roles and val_str != "None":
                target_roles.append(val_str)

    for role_val in sorted(target_roles, key=lambda x: int(x) if x.isdigit() else 999):
        user_roles_data[role_val] = {
            "label": "",
            "description": f"Placeholder mapping for user_role={role_val}",
            "business_category": ""
        }

    # 2. Reference Type Categorizations (Earnings vs Redemptions)
    reference_types_data = {}
    ref_profile = profile_data.get("targeted_columns", {}).get("wallet_transaction.reference_type") or \
                  profile_data.get("all_low_cardinality_columns", {}).get("wallet_transaction.reference_type", {})

    # Default catalog of reference types
    default_ref_types = {
        "cash_point": {"categorization": "Earnings", "description": "Points earned via QR scan"},
        "withdrawal": {"categorization": "Redemptions", "description": "Cash payout withdrawal request"},
        "topup": {"categorization": "Earnings", "description": "Wallet balance topup credit"},
        "credit_note": {"categorization": "Earnings", "description": "System credit note adjustment"},
        "incentive": {"categorization": "Earnings", "description": "Mechanic or retailer incentive credit"},
        "bonus_conversion": {"categorization": "Earnings", "description": "Bonus point conversion to cash balance"},
        "referral_earning": {"categorization": "Earnings", "description": "User referral reward earning"}
    }

    if ref_profile and "distinct_values" in ref_profile:
        for item in ref_profile["distinct_values"]:
            rval = str(item["value"])
            if rval and rval != "None":
                if rval in default_ref_types:
                    reference_types_data[rval] = default_ref_types[rval]
                else:
                    reference_types_data[rval] = {
                        "categorization": "",
                        "description": f"Placeholder mapping for reference_type='{rval}' (Earnings vs Redemptions)"
                    }
    else:
        reference_types_data = default_ref_types

    # 3. Core Business Metrics Definitions
    metrics_definitions = {
        "Balance": {
            "definition": "Current net wallet cash balance across active users in rupees",
            "sql_expression": "SUM(wallet_balance)",
            "table": "users",
            "column": "wallet_balance",
            "unit": "INR",
            "notes": "Placeholder definition for wallet balance metric"
        },
        "Retailer Box Scans": {
            "definition": "Total count of SKU inventories scanned or ordered by retailers",
            "sql_expression": "COUNT(CASE WHEN order_type IN ('Retailer', 'retailer') THEN 1 END)",
            "table": "sku_inventories",
            "column": "order_type",
            "unit": "Scans",
            "notes": "Placeholder definition for Retailer Box Scans metric"
        },
        "Wholesaler Box Scans": {
            "definition": "Total count of SKU inventories scanned or ordered by wholesalers/distributors",
            "sql_expression": "COUNT(CASE WHEN order_type IN ('Wholesaler', 'Distributor', 'Distributors') THEN 1 END)",
            "table": "sku_inventories",
            "column": "order_type",
            "unit": "Scans",
            "notes": "Placeholder definition for Wholesaler Box Scans metric"
        }
    }

    # Construct complete dictionary structure
    business_dictionary = {
        "_metadata": {
            "title": "JGH Intelligence Engine - Business Terms & Metrics Dictionary Template",
            "generated_at": datetime.now().isoformat(),
            "version": "0.1.0-draft",
            "status": "READY_FOR_HUMAN_LABELING"
        },
        "user_role_mappings": user_roles_data,
        "reference_type_categorizations": reference_types_data,
        "core_metrics": metrics_definitions
    }

    output_path = KNOWLEDGE_DIR / "business_dictionary.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(business_dictionary, f, indent=2)

    print(f"[OK] Saved draft business dictionary template to {output_path.relative_to(PROJECT_ROOT)}")
    print("\n" + "=" * 60)
    print(" ✅ Business Dictionary Template Ready for Human Labeling!")
    print("=" * 60)

if __name__ == "__main__":
    generate_draft_dictionary()
