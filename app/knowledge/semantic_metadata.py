import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Canonical Business Semantic Metadata Schema
# Derives meanings strictly from schema, relationships, and domain specs.
BUSINESS_SEMANTIC_METADATA: Dict[str, Dict[str, Any]] = {
    "sku_inventories": {
        "table_name": "sku_inventories",
        "description": "Physical inventory items, box dispatch logs, and box scanning events",
        "entity_type": "box_scan",
        "primary_key": "id",
        "temporal_column": "retailer_scanned_at",
        "columns": {
            "id": {
                "column": "id",
                "data_type": "INTEGER",
                "primary_key": True,
                "foreign_key": False,
                "references": None,
                "description": "Unique identifier for the SKU inventory box record",
                "business_meaning": "Identifies an individual box or box scan record",
                "synonyms": ["box", "box scan", "scanned box", "box id", "scan record", "inventory id"],
                "entity_type": "box",
                "metric_type": "count",
                "temporal_role": None
            },
            "lpn_number": {
                "column": "lpn_number",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "License Plate Number / QR barcode printed on the box",
                "business_meaning": "Unique scannable barcode identifying an individual box",
                "synonyms": ["barcode", "lpn", "box barcode", "qr code", "scanned box code"],
                "entity_type": "box",
                "metric_type": "identifier",
                "temporal_role": None
            },
            "retailer_scanned_at": {
                "column": "retailer_scanned_at",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Timestamp when a retailer scanned the box QR code",
                "business_meaning": "Records the date and time when the box was scanned by a retailer",
                "synonyms": ["scanned at", "scan date", "scan time", "date of scan", "scan timestamp", "retailer scan date"],
                "entity_type": "temporal",
                "metric_type": None,
                "temporal_role": "event_timestamp"
            },
            "wholesaler_scanned_at": {
                "column": "wholesaler_scanned_at",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Timestamp when a wholesaler scanned the box",
                "business_meaning": "Records date and time when the box was scanned by a wholesaler",
                "synonyms": ["wholesaler scan date", "wholesaler scan time"],
                "entity_type": "temporal",
                "metric_type": None,
                "temporal_role": "event_timestamp"
            },
            "status_retailer_id": {
                "column": "status_retailer_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": True,
                "references": {"table": "users", "column": "id"},
                "description": "User ID of the retailer who completed the scan",
                "business_meaning": "Connects a scanned box to the retailer who scanned it",
                "synonyms": ["retailer id", "scanning retailer", "retailer", "retailer user id"],
                "entity_type": "retailer",
                "metric_type": None,
                "temporal_role": None
            },
            "distributer_id": {
                "column": "distributer_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": True,
                "references": {"table": "users", "column": "id"},
                "description": "User ID of the distributor who supplied/dispatched the inventory",
                "business_meaning": "Connects a scanned box to the supplying distributor",
                "synonyms": ["distributor id", "distributor", "supplying distributor", "dispatch distributor"],
                "entity_type": "distributor",
                "metric_type": None,
                "temporal_role": None
            },
            "sku_code": {
                "column": "sku_code",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "SKU catalog code identifying product item variant",
                "business_meaning": "Stock keeping unit product code for the scanned box",
                "synonyms": ["sku", "sku code", "product code", "item code"],
                "entity_type": "product",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "sku_description": {
                "column": "sku_description",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Product category and item description",
                "business_meaning": "Human-readable description representing the product line, brand, and category of the box",
                "synonyms": ["category", "product category", "description", "item name", "product name", "box category"],
                "entity_type": "category",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "product_id": {
                "column": "product_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": False,
                "references": {"table": "products", "column": "id"},
                "description": "Foreign identifier pointing to the product catalog",
                "business_meaning": "Connects box inventory to the central product master",
                "synonyms": ["product id", "product"],
                "entity_type": "product",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "uom": {
                "column": "uom",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Unit of Measure / packaging configuration (e.g. B10 = Box of 10, B5 = Box of 5)",
                "business_meaning": "Packaging unit of measure for the box",
                "synonyms": ["unit of measure", "uom", "box type", "packaging"],
                "entity_type": "packaging",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "created_at": {
                "column": "created_at",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Inventory record creation timestamp",
                "business_meaning": "Timestamp when the inventory record was first created",
                "synonyms": ["inventory created at"],
                "entity_type": "temporal",
                "metric_type": None,
                "temporal_role": "record_timestamp"
            }
        }
    },
    "users": {
        "table_name": "users",
        "description": "Platform users including retailers, distributors, wholesalers, and mechanics",
        "entity_type": "user",
        "primary_key": "id",
        "temporal_column": "created_at",
        "columns": {
            "id": {
                "column": "id",
                "data_type": "INTEGER",
                "primary_key": True,
                "foreign_key": False,
                "references": None,
                "description": "Unique user identifier",
                "business_meaning": "Unique ID identifying any business actor (retailer, distributor, wholesaler)",
                "synonyms": ["user id", "retailer id", "distributor id", "partner id"],
                "entity_type": "user",
                "metric_type": "identifier",
                "temporal_role": None
            },
            "name": {
                "column": "name",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Name of the retailer, distributor, or business entity",
                "business_meaning": "Display name of the retailer or distributor business",
                "synonyms": ["name", "retailer name", "distributor name", "business name", "shop name"],
                "entity_type": "user",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "user_role": {
                "column": "user_role",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Actor role classification: 2 = Retailer, 4 = Distributor, 5 = Wholesaler, 3 = Mechanic",
                "business_meaning": "Defines the role of the user (2: retailer, 4: distributor)",
                "synonyms": ["role", "user role", "actor type"],
                "entity_type": "role",
                "metric_type": "filter",
                "temporal_role": None
            },
            "state_id": {
                "column": "state_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Geographical state numerical identifier (e.g. 11 = Karnataka, 12 = Kerala, 14 = Maharashtra)",
                "business_meaning": "Identifies the geographic state where the retailer or distributor operates",
                "synonyms": ["state", "state id", "retailer state", "region", "geography"],
                "entity_type": "state",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "city": {
                "column": "city",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "City where the user operates",
                "business_meaning": "City location of the user",
                "synonyms": ["city", "town", "location"],
                "entity_type": "city",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "district": {
                "column": "district",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Administrative district of the user",
                "business_meaning": "District location of the user",
                "synonyms": ["district"],
                "entity_type": "district",
                "metric_type": "dimension",
                "temporal_role": None
            },
            "wallet_balance": {
                "column": "wallet_balance",
                "data_type": "REAL",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Current monetary wallet balance",
                "business_meaning": "Current unspent wallet balance amount",
                "synonyms": ["wallet balance", "balance", "funds"],
                "entity_type": "balance",
                "metric_type": "measure",
                "temporal_role": None
            },
            "created_at": {
                "column": "created_at",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "User registration timestamp",
                "business_meaning": "Date when the user registered in the system",
                "synonyms": ["registered at", "onboarded at"],
                "entity_type": "temporal",
                "metric_type": None,
                "temporal_role": "record_timestamp"
            }
        }
    },
    "retailer_distributor_mappings": {
        "table_name": "retailer_distributor_mappings",
        "description": "Mapping hierarchy linking retailers to their assigned distributors",
        "entity_type": "relationship",
        "primary_key": "id",
        "temporal_column": "created_at",
        "columns": {
            "id": {
                "column": "id",
                "data_type": "INTEGER",
                "primary_key": True,
                "foreign_key": False,
                "references": None,
                "description": "Mapping record identifier",
                "business_meaning": "Unique ID for the retailer-distributor linkage",
                "synonyms": ["mapping id"],
                "entity_type": "mapping",
                "metric_type": "identifier",
                "temporal_role": None
            },
            "retailer_id": {
                "column": "retailer_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": True,
                "references": {"table": "users", "column": "id"},
                "description": "Retailer ID linked to the distributor",
                "business_meaning": "Retailer user ID in the relationship",
                "synonyms": ["retailer id", "retailer", "mapped retailer"],
                "entity_type": "retailer",
                "metric_type": None,
                "temporal_role": None
            },
            "distributor_id": {
                "column": "distributor_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": True,
                "references": {"table": "users", "column": "id"},
                "description": "Distributor ID assigned to the retailer",
                "business_meaning": "Distributor user ID in the relationship",
                "synonyms": ["distributor id", "distributor", "parent distributor", "assigned distributor"],
                "entity_type": "distributor",
                "metric_type": None,
                "temporal_role": None
            }
        }
    },
    "wallet_transaction": {
        "table_name": "wallet_transaction",
        "description": "Financial ledger storing wallet credits, debit transactions, and cash points",
        "entity_type": "financial_ledger",
        "primary_key": "id",
        "temporal_column": "created_at",
        "columns": {
            "id": {
                "column": "id",
                "data_type": "INTEGER",
                "primary_key": True,
                "foreign_key": False,
                "references": None,
                "description": "Transaction ledger identifier",
                "business_meaning": "Unique ID for a financial ledger transaction",
                "synonyms": ["transaction id"],
                "entity_type": "transaction",
                "metric_type": "identifier",
                "temporal_role": None
            },
            "user_id": {
                "column": "user_id",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": True,
                "references": {"table": "users", "column": "id"},
                "description": "User who owns the transaction",
                "business_meaning": "Identifies the user account whose balance was credited/debited",
                "synonyms": ["user id", "account holder"],
                "entity_type": "user",
                "metric_type": None,
                "temporal_role": None
            },
            "amount": {
                "column": "amount",
                "data_type": "REAL",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Monetary value credited or debited",
                "business_meaning": "Monetary amount of earnings, rewards, or withdrawals",
                "synonyms": ["earnings", "amount", "value", "wallet amount", "transaction value"],
                "entity_type": "currency",
                "metric_type": "measure",
                "temporal_role": None
            },
            "transaction_type": {
                "column": "transaction_type",
                "data_type": "INTEGER",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Type: 1 = Credit (earnings/points), 0 = Debit (withdrawal)",
                "business_meaning": "Distinguishes credit earnings (1) from withdrawals (0)",
                "synonyms": ["credit debit flag", "transaction type"],
                "entity_type": "flag",
                "metric_type": "filter",
                "temporal_role": None
            },
            "created_at": {
                "column": "created_at",
                "data_type": "TEXT",
                "primary_key": False,
                "foreign_key": False,
                "references": None,
                "description": "Timestamp when the transaction occurred",
                "business_meaning": "Date and time of the wallet transaction",
                "synonyms": ["transaction date", "transaction time", "earned at"],
                "entity_type": "temporal",
                "metric_type": None,
                "temporal_role": "event_timestamp"
            }
        }
    },
    "companies": {
        "table_name": "companies",
        "description": "Company corporate accounts and enterprise business units",
        "entity_type": "company",
        "primary_key": "id",
        "temporal_column": "created_at",
        "columns": {
            "id": {"column": "id", "data_type": "INTEGER", "primary_key": True, "business_meaning": "Company ID", "synonyms": ["company id"]},
            "name": {"column": "name", "data_type": "TEXT", "business_meaning": "Company name", "synonyms": ["company name", "enterprise name"]},
            "business_unit": {"column": "business_unit", "data_type": "TEXT", "business_meaning": "Business division", "synonyms": ["business unit"]}
        }
    }
}


def calculate_dynamic_time_range(period_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculates dynamic datetime boundaries at runtime without hardcoding static dates.
    For 'this month' or 'current month': uses current runtime month.
    For 'last month' or 'previous month': uses previous runtime month.
    For explicit month (e.g. 'July 2026'): uses the explicitly requested month.
    """
    import re
    from datetime import datetime
    p_lower = (period_str or "").lower().strip()
    now = datetime.now()

    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
    }

    # 1. Explicit month mentioned
    matched_month = None
    for m_name, m_num in month_map.items():
        if m_name in p_lower:
            matched_month = m_num
            break

    y_match = re.search(r"\b(202\d)\b", p_lower)
    year = int(y_match.group(1)) if y_match else now.year

    if matched_month:
        st = datetime(year, matched_month, 1, 0, 0, 0)
        en = datetime(year + 1, 1, 1, 0, 0, 0) if matched_month == 12 else datetime(year, matched_month + 1, 1, 0, 0, 0)
        return {
            "start": st.strftime("%Y-%m-%d %H:%M:%S"),
            "end": en.strftime("%Y-%m-%d %H:%M:%S"),
            "label": f"{list(month_map.keys())[matched_month - 1].capitalize()} {year}",
            "type": "explicit_month"
        }

    # 2. Relative two-month comparison (e.g. 'previous month and current month')
    if ("last month" in p_lower or "previous month" in p_lower) and ("this month" in p_lower or "current month" in p_lower):
        lm_year = now.year - 1 if now.month == 1 else now.year
        lm_month = 12 if now.month == 1 else now.month - 1
        st = datetime(lm_year, lm_month, 1, 0, 0, 0)
        en = datetime(now.year + 1, 1, 1, 0, 0, 0) if now.month == 12 else datetime(now.year, now.month + 1, 1, 0, 0, 0)
        return {
            "start": st.strftime("%Y-%m-%d %H:%M:%S"),
            "end": en.strftime("%Y-%m-%d %H:%M:%S"),
            "label": "previous month vs current month",
            "type": "relative_comparison_two_months"
        }

    # 3. Relative 'last month'
    if "last month" in p_lower or "previous month" in p_lower:
        lm_year = now.year - 1 if now.month == 1 else now.year
        lm_month = 12 if now.month == 1 else now.month - 1
        st = datetime(lm_year, lm_month, 1, 0, 0, 0)
        en = datetime(now.year, now.month, 1, 0, 0, 0)
        return {
            "start": st.strftime("%Y-%m-%d %H:%M:%S"),
            "end": en.strftime("%Y-%m-%d %H:%M:%S"),
            "label": "last month",
            "type": "relative_last_month"
        }

    # 3. Relative 'this month' or default
    st = datetime(now.year, now.month, 1, 0, 0, 0)
    en = datetime(now.year + 1, 1, 1, 0, 0, 0) if now.month == 12 else datetime(now.year, now.month + 1, 1, 0, 0, 0)
    return {
        "start": st.strftime("%Y-%m-%d %H:%M:%S"),
        "end": en.strftime("%Y-%m-%d %H:%M:%S"),
        "label": "this month",
        "type": "relative_current_month"
    }


def find_metric_source(metric_name: str) -> Optional[Dict[str, Any]]:
    """
    Finds verified table, column, and aggregation for a business metric concept.
    Strictly keeps sku_inventories (box_scans) and wallet_transaction (earnings) isolated.
    """
    m_clean = (metric_name or "").lower().strip()
    if any(k in m_clean for k in ["box scan", "box scans", "boxes scanned", "scanned box", "scanned boxes", "scan", "scans", "box"]):
        return {
            "metric": "box_scan_count",
            "table": "qr_point_map",
            "column": "box_calulation_um",
            "metric_source": "qr_point_map.box_calulation_um",
            "aggregation": "SUM",
            "join_table": "sku_inventories",
            "join_condition": "sku_inventories.sku_code = qr_point_map.sku_code",
            "temporal_column": "sku_inventories.retailer_scanned_at",
            "date_column": "retailer_scanned_at",
            "business_meaning": "Authoritative box quantity calculated as SUM(qr_point_map.box_calulation_um) joined on sku_inventories.sku_code = qr_point_map.sku_code"
        }
    if any(k in m_clean for k in ["earning", "earnings", "wallet amount", "revenue", "reward"]):
        return {
            "metric": "earnings",
            "table": "wallet_transaction",
            "column": "amount",
            "metric_source": "wallet_transaction.amount",
            "aggregation": "SUM",
            "filter": "reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem') AND amount > 0",
            "temporal_column": "wallet_transaction.created_at",
            "date_column": "created_at",
            "business_meaning": "Sum of positive credit amounts in wallet_transaction with reference_type in ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')"
        }
    if any(k in m_clean for k in ["wallet balance", "balance"]):
        return {
            "metric": "wallet_balance",
            "table": "users",
            "column": "wallet_balance",
            "metric_source": "users.wallet_balance",
            "aggregation": "SUM",
            "temporal_column": None,
            "business_meaning": "Current wallet balance stored on user account"
        }
    if any(k in m_clean for k in ["count", "number of"]):
        return {
            "metric": "count",
            "table": None,  # Grounded from entity/dimension
            "column": "*",
            "metric_source": "*",
            "aggregation": "COUNT",
            "temporal_column": None,
            "business_meaning": "Entity row count"
        }
    return None


def find_dimension_source(dimension_name: str) -> Optional[Dict[str, Any]]:
    """
    Finds verified table, column, and foreign-key link for a requested dimension.
    """
    d_clean = (dimension_name or "").lower().strip()
    if d_clean in ["retailer", "retailers"]:
        return {
            "dimension": "retailer",
            "table": "users",
            "column": "id",
            "name_column": "name",
            "role_filter": "user_role = 2",
            "dimension_source": "users.id",
            "join_to_sku_inventories": "sku_inventories.status_retailer_id = users.id",
            "join_to_mappings": "retailer_distributor_mappings.retailer_id = users.id",
            "business_meaning": "Retailer in users table"
        }
    if d_clean in ["distributor", "distributors"]:
        return {
            "dimension": "distributor",
            "table": "users",
            "column": "id",
            "name_column": "name",
            "role_filter": "user_role = 4",
            "dimension_source": "users.id",
            "join_to_sku_inventories": "sku_inventories.distributer_id = users.id",
            "join_to_mappings": "retailer_distributor_mappings.distributor_id = users.id",
            "business_meaning": "Distributor in users table"
        }
    if d_clean in ["wholesaler", "wholesalers"]:
        return {
            "dimension": "wholesaler",
            "table": "users",
            "column": "id",
            "name_column": "name",
            "role_filter": "user_role = 5",
            "dimension_source": "users.id",
            "business_meaning": "Wholesaler in users table"
        }
    if d_clean in ["state", "states", "region"]:
        return {
            "dimension": "state",
            "table": "users",
            "column": "state_id",
            "dimension_source": "users.state_id",
            "join_to_sku_inventories": "sku_inventories.status_retailer_id = users.id",
            "business_meaning": "State numerical ID in users table via retailer"
        }
    if d_clean in ["category", "categories", "product line", "product"]:
        return {
            "dimension": "category",
            "table": "sku_inventories",
            "column": "sku_description",
            "dimension_source": "sku_inventories.sku_description",
            "join_to_sku_inventories": None,  # Already on sku_inventories
            "business_meaning": "Product category and description in sku_inventories"
        }
    if d_clean in ["company", "companies"]:
        return {
            "dimension": "company",
            "table": "companies",
            "column": "id",
            "name_column": "name",
            "dimension_source": "companies.id",
            "business_meaning": "Company record in companies table"
        }
    return None



def get_semantic_schema_context() -> str:
    """Returns compact formatted semantic metadata for LLM grounding."""
    lines = ["VERIFIED DATABASE SCHEMA & BUSINESS SEMANTIC METADATA:"]
    for tname, tinfo in BUSINESS_SEMANTIC_METADATA.items():
        lines.append(f"\nTABLE: {tname} — {tinfo['description']}")
        lines.append(f"  Primary Key: {tinfo.get('primary_key')}")
        lines.append(f"  Event Timestamp: {tinfo.get('temporal_column')}")
        lines.append("  Columns:")
        for cname, cinfo in tinfo.get("columns", {}).items():
            ref = f" (FK -> {cinfo['references']['table']}.{cinfo['references']['column']})" if cinfo.get("references") else ""
            bm = cinfo.get("business_meaning", "UNKNOWN")
            syns = ", ".join(cinfo.get("synonyms", [])[:4])
            lines.append(f"    - {cname} ({cinfo.get('data_type', 'TEXT')}){ref}: {bm} [Synonyms: {syns}]")
    return "\n".join(lines)


def answer_schema_question(question: str) -> Optional[Dict[str, Any]]:
    """
    Answers schema knowledge and relationship discovery questions directly from
    verified semantic metadata without requiring SQL generation.
    Never hijacks analytical queries (highest, lowest, top, compare, this month, etc.).
    """
    q_low = question.lower().strip()

    # Guard: Never hijack analytical business queries unless explicitly inquiring about schema relationships
    if "relationship" not in q_low:
        analytical_signals = [
            "highest", "lowest", "top", "bottom", "most", "least", "compare",
            "show all", "generate", "this month", "last month",
            "how many", "total", "sum", "count"
        ]
        if any(sig in q_low for sig in analytical_signals):
            return None

    # 1. Tables containing box scan information
    if "box scan" in q_low and any(w in q_low for w in ["what table", "which table", "tables contain", "where are"]):
        return {
            "answer": "Individual box scan events and physical box inventories are stored in the `sku_inventories` table. Associated user and partner profiles (retailers, distributors) are stored in `users`.",
            "tables": ["sku_inventories", "users"],
            "primary_table": "sku_inventories"
        }

    # 2. Individual box scan records
    if any(w in q_low for w in ["individual", "single", "each box"]) and "box" in q_low and any(w in q_low for w in ["table", "store", "where"]):
        return {
            "answer": "Individual box scan records are stored in `sku_inventories`, where each row represents a distinct physical box identified by primary key `id` and barcode `lpn_number`.",
            "tables": ["sku_inventories"],
            "primary_table": "sku_inventories"
        }

    # 3. Box scan timestamp
    if ("timestamp" in q_low or "scanned_at" in q_low or ("date" in q_low and "scan" in q_low) or "time of scan" in q_low):
        if "sku_inventories" in q_low or "box" in q_low:
            return {
                "answer": "In `sku_inventories`, the retailer scan timestamp is recorded in the `retailer_scanned_at` column. Wholesaler scans are recorded in `wholesaler_scanned_at`.",
                "tables": ["sku_inventories"],
                "column": "retailer_scanned_at"
            }

    # 4. Links to retailer
    if ("retailer" in q_low) and any(w in q_low for w in ["which column", "what column", "foreign key", "column links", "column connects", "who scanned"]):
        if "box" in q_low or "sku_inventories" in q_low:
            return {
                "answer": "In `sku_inventories`, the column `status_retailer_id` links the box scan to the retailer who scanned it (`users.id` where `user_role = 2`).",
                "tables": ["sku_inventories", "users"],
                "column": "status_retailer_id",
                "foreign_key": "sku_inventories.status_retailer_id -> users.id"
            }

    # 5. Links to distributor
    if ("distributor" in q_low or "distributer" in q_low) and any(w in q_low for w in ["which column", "what column", "foreign key", "column links", "column connects", "supplied"]):
        if "box" in q_low or "sku_inventories" in q_low:
            return {
                "answer": "In `sku_inventories`, the column `distributer_id` links the box inventory to the supplying distributor (`users.id` where `user_role = 4`).",
                "tables": ["sku_inventories", "users"],
                "column": "distributer_id",
                "foreign_key": "sku_inventories.distributer_id -> users.id"
            }

    # 6. Product or category
    if any(w in q_low for w in ["category", "product", "item"]) and any(w in q_low for w in ["which column", "what column", "column indicates", "column represents", "field indicates"]):
        return {
            "answer": "In `sku_inventories`, the column `sku_description` stores the human-readable product category and item description. The column `sku_code` contains the catalog SKU code, and `product_id` references the product catalog.",
            "tables": ["sku_inventories"],
            "column": "sku_description"
        }

    # 7. Relationship between sku_inventories and users
    if "relationship" in q_low and "sku_inventories" in q_low and "users" in q_low:
        return {
            "answer": "The relationship between `sku_inventories` and `users` is established through two foreign keys: `sku_inventories.status_retailer_id -> users.id` (links to the scanning retailer) and `sku_inventories.distributer_id -> users.id` (links to the supplying distributor).",
            "tables": ["sku_inventories", "users"],
            "relationships": [
                "sku_inventories.status_retailer_id = users.id (Retailer, user_role=2)",
                "sku_inventories.distributer_id = users.id (Distributor, user_role=4)"
            ]
        }

    # 8. Relationship between sku_inventories and retailer_distributor_mappings
    if "relationship" in q_low and "sku_inventories" in q_low and any(w in q_low for w in ["retailer_distributor_mappings", "mappings", "mapping"]):
        return {
            "answer": "`sku_inventories` connects to `retailer_distributor_mappings` via the `users` table: `sku_inventories.status_retailer_id = retailer_distributor_mappings.retailer_id` and `sku_inventories.distributer_id = retailer_distributor_mappings.distributor_id`.",
            "tables": ["sku_inventories", "retailer_distributor_mappings", "users"],
            "relationships": [
                "sku_inventories.status_retailer_id = retailer_distributor_mappings.retailer_id",
                "sku_inventories.distributer_id = retailer_distributor_mappings.distributor_id"
            ]
        }

    return None

