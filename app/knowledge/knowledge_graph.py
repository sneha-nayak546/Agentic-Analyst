import os
import re
import json
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

MONTH_MAP = {
    "january": ("01-01", "02-01"), "jan": ("01-01", "02-01"),
    "february": ("02-01", "03-01"), "feb": ("02-01", "03-01"),
    "march": ("03-01", "04-01"), "mar": ("03-01", "04-01"),
    "april": ("04-01", "05-01"), "apr": ("04-01", "05-01"),
    "may": ("05-01", "06-01"),
    "june": ("06-01", "07-01"), "jun": ("06-01", "07-01"),
    "july": ("07-01", "08-01"), "jul": ("07-01", "08-01"),
    "august": ("08-01", "09-01"), "aug": ("08-01", "09-01"),
    "september": ("09-01", "10-01"), "sep": ("09-01", "10-01"), "sept": ("09-01", "10-01"),
    "october": ("10-01", "11-01"), "oct": ("10-01", "11-01"),
    "november": ("11-01", "12-01"), "nov": ("11-01", "12-01"),
    "december": ("12-01", "01-01"), "dec": ("12-01", "01-01")
}

# Non-technical user term mappings to tables
USER_FRIENDLY_TABLE_ALIASES = {
    "users": [
        "user", "users", "customer", "customers", "client", "clients",
        "retailer", "retailers", "shop owner", "shop owners", "shopkeeper", "shopkeepers",
        "dealer", "dealers", "wholesaler", "wholesalers",
        "distributor", "distributors", "mechanic", "mechanics",
        "member", "members", "account", "accounts", "registered user", "registered users",
        "people", "person", "who", "everyone", "all users", "all retailers"
    ],
    "wallet_transaction": [
        "wallet", "transaction", "transactions", "balance", "fund", "funds",
        "point", "points", "cash point", "cash_point", "cashpoint",
        "earning", "earnings", "earn", "earned", "how much earned",
        "topup", "top up", "top-up", "recharge",
        "coupon", "coupon_redeem", "coupon redeem", "redeem", "redemption",
        "reward", "rewards", "cashback", "cash back",
        "referral", "referral earning", "referral_earning", "referred",
        "scan earning", "qr scan",
        "withdrawal", "withdraw", "withdrawals", "payout", "payouts",
        "credit", "debit", "money", "amount", "payment", "paid",
        "how much", "total earned", "total amount"
    ],
    "sku_qr_points_map": [
        "sku_qr_points_map", "qr_points_map", "box_scanning", "scanned_boxes",
        "qr_points", "sku_points", "sku_scanned_boxes", "box scans", "box uom",
        "box_calculation_uom", "gride_type", "wholesaler_scanned_at", "retailer_scanned_at",
        "scanned_boxes_retailer", "scanned_boxes_wholesaler", "scanned boxes retailer",
        "scanned boxes wholesaler", "retailer box scans", "wholesaler box scans"
    ],
    "sku_inventories": [
        "sku", "inventory", "inventories", "product", "products", "item", "items", "carton", "lpn", "barcode",
        "sku_inventories", "sku inventories", "wholesaler_scanned_at", "retailer_scanned_at",
        "scanned_boxes_retailer", "scanned_boxes_wholesaler", "scanned boxes retailer",
        "scanned boxes wholesaler", "retailer box scans", "wholesaler box scans",
        "scan", "scans", "scanning", "scanned", "scanning report", "scan report", "box scan", "box scans"
    ]
}

class BusinessKnowledgeGraph:
    def __init__(self):
        self.schema_meta = {}
        self.entity_dict = {}
        self.column_dict = {}
        self.business_meta = {}
        self.enum_meta = {}
        self.sample_values = {}
        self.query_patterns = {}
        self.execution_history = {}
        
        self.nodes = {}
        self.edges = []
        self.join_graph = defaultdict(list)
        
        self.load_metadata()
        self.build_graph()

    def load_json(self, path: str) -> dict:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {path}: {e}")
        return {}

    def load_metadata(self):
        self.schema_meta = self.load_json("knowledge/schema/schema_metadata.json")
        self.entity_dict = self.load_json("knowledge/graph/entity_dictionary.json")
        self.column_dict = self.load_json("knowledge/graph/column_dictionary.json")
        self.business_meta = self.load_json("knowledge/graph/business_dictionary.json")
        self.enum_meta = self.load_json("knowledge/schema/enum_dictionary.json")
        self.sample_values = self.load_json("knowledge/schema/sample_values.json")
        self.query_patterns = self.load_json("knowledge/patterns/query_patterns.json")
        self.execution_history = self.load_json("knowledge/history/execution_history.json")

    def build_graph(self):
        # 1. Register Table Nodes
        for tbl_name, info in self.schema_meta.items():
            self.nodes[f"table:{tbl_name}"] = {
                "id": f"table:{tbl_name}",
                "type": "Table",
                "name": tbl_name
            }
            
            # Explicit Foreign Keys
            for fk in info.get("foreign_keys", []):
                ref_table = fk['referred_table']
                for src_col, ref_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    self.add_edge(tbl_name, ref_table, src_col, ref_col, "explicit_fk")
        
        # 2. Infer Missing Relationships via Column Dictionary
        for col_name, tables in self.column_dict.items():
            # If a column like 'user_id' appears in multiple tables, link them if one is 'users'
            if col_name.endswith("_id"):
                base_entity = col_name[:-3]
                base_table_candidates = [t for t in tables if t['table'] == base_entity or t['table'] == base_entity + "s"]
                if base_table_candidates:
                    ref_table = base_table_candidates[0]['table']
                    for t in tables:
                        if t['table'] != ref_table:
                            self.add_edge(t['table'], ref_table, col_name, 'id', "inferred_fk")

        # 3. Explicit Graph Edges for sku_inventories, sku_qr_points_map & Dual-Role Box Scanning
        self.add_edge("sku_inventories", "sku_qr_points_map", "sku_code", "sku_code", "explicit_fk")
        self.add_edge("sku_inventories", "users", "status_retailer_id", "id", "explicit_fk")
        self.add_edge("sku_inventories", "users", "status_wholeseller_id", "id", "explicit_fk")
        self.add_edge("sku_inventories", "users", "distributer_id", "id", "explicit_fk")
        self.add_edge("sku_qr_points_map", "sku_inventories", "sku_code", "sku_code", "explicit_fk")
        self.add_edge("sku_qr_points_map", "users", "status_wholesaler_id", "id", "explicit_fk")
        self.add_edge("sku_qr_points_map", "users", "status_retailer_id", "id", "explicit_fk")
        
        # 3. Save Relationship Metadata
        os.makedirs("knowledge/graph", exist_ok=True)
        with open("knowledge/graph/join_graph.json", "w") as f:
            json.dump(self.join_graph, f, indent=4)
            
        with open("knowledge/graph/relationship_metadata.json", "w") as f:
            json.dump(self.edges, f, indent=4)

    def add_edge(self, from_tbl: str, to_tbl: str, from_col: str, to_col: str, edge_type: str):
        edge = {
            "from": f"table:{from_tbl}",
            "to": f"table:{to_tbl}",
            "type": edge_type,
            "join_clause": f"{from_tbl}.{from_col} = {to_tbl}.{to_col}"
        }
        if edge not in self.edges:
            self.edges.append(edge)
            self.join_graph[from_tbl].append(to_tbl)
            self.join_graph[to_tbl].append(from_tbl) # undirected for searching paths

    def bfs_shortest_path(self, start: str, target: str) -> List[str]:
        queue = [(start, [start])]
        visited = set([start])
        while queue:
            node, path = queue.pop(0)
            if node == target:
                return path
            for neighbor in self.join_graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []

    def get_join_clauses_for_path(self, path: List[str]) -> List[str]:
        joins = []
        for i in range(len(path) - 1):
            t1, t2 = path[i], path[i+1]
            for edge in self.edges:
                if (edge["from"] == f"table:{t1}" and edge["to"] == f"table:{t2}") or \
                   (edge["from"] == f"table:{t2}" and edge["to"] == f"table:{t1}"):
                    joins.append(f"JOIN {t2} ON {edge['join_clause']}" if edge["from"]==f"table:{t1}" else f"JOIN {t1} ON {edge['join_clause']}")
                    break
        return list(set(joins))

    def resolve_date_range(self, question: str) -> Tuple[str, str, str]:
        q_lower = question.lower()
        import datetime
        today = datetime.date.today()

        if "today" in q_lower:
            start_date = today.strftime("%Y-%m-%d")
            end_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            return "today", start_date, end_date

        if "yesterday" in q_lower:
            yesterday = today - datetime.timedelta(days=1)
            start_date = yesterday.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            return "yesterday", start_date, end_date

        if "this week" in q_lower or "current week" in q_lower:
            start_date = (today - datetime.timedelta(days=today.weekday())).strftime("%Y-%m-%d")
            end_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            return "this week", start_date, end_date

        if "last week" in q_lower or "previous week" in q_lower:
            start_of_this_week = today - datetime.timedelta(days=today.weekday())
            start_date = (start_of_this_week - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = start_of_this_week.strftime("%Y-%m-%d")
            return "last week", start_date, end_date

        if "last 7 days" in q_lower or "past 7 days" in q_lower:
            start_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            return "last 7 days", start_date, end_date

        if "last 30 days" in q_lower or "past 30 days" in q_lower:
            start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            return "last 30 days", start_date, end_date

        if "this month" in q_lower or "current month" in q_lower:
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            next_month = today.replace(day=28) + datetime.timedelta(days=4)
            end_date = next_month.replace(day=1).strftime("%Y-%m-%d")
            return "this month", start_date, end_date
            
        if "last month" in q_lower or "previous month" in q_lower:
            first = today.replace(day=1)
            last_month = first - datetime.timedelta(days=1)
            start_date = last_month.replace(day=1).strftime("%Y-%m-%d")
            end_date = first.strftime("%Y-%m-%d")
            return "last month", start_date, end_date
            
        for m_name, (start_m, end_m) in MONTH_MAP.items():
            if re.search(rf"\b{m_name}\b", q_lower):
                match_y = re.search(r"\b(20\d{2})\b", q_lower)
                year = match_y.group(1) if match_y else str(today.year)
                start_date = f"{year}-{start_m}"
                end_date = f"{year}-{end_m}" if m_name not in ["december", "dec"] else f"{int(year)+1}-01-01"
                return m_name, start_date, end_date
        return None, None, None

    def resolve_business_query(self, question: str) -> dict:
        q_lower = question.lower()
        detected_tables = set()
        
        # Aliases for target enterprise tables — includes non-technical user-friendly terms
        aliases = {
            "users": USER_FRIENDLY_TABLE_ALIASES["users"] + [
                "retailer", "retailers", "wholesaler", "wholesalers",
                "distributor", "distributors", "mechanic", "mechanics",
                "shop owner", "shop owners", "shopkeeper", "dealer", "dealers"
            ],
            "wallet_transaction": USER_FRIENDLY_TABLE_ALIASES["wallet_transaction"] + [
                "wallet", "transaction", "transactions", "cash point", "cash_point",
                "earning", "earnings", "earn", "earned", "referral", "referral earning",
                "topup", "top up", "coupon", "coupon_redeem", "coupon redeem",
                "cashback", "cash back", "reward", "rewards", "payout", "payouts",
                "withdrawal", "withdrawals", "credit", "debit", "payment"
            ],
            "sku_inventories": USER_FRIENDLY_TABLE_ALIASES["sku_inventories"] + ["sku", "inventory", "inventories", "product", "products", "item", "items", "carton", "lpn", "barcode", "scanned_boxes_retailer", "scanned_boxes_wholesaler", "scan", "scans", "scanning", "scanned", "scanning report", "scan report", "box scan", "box scans"],
            "companies": ["company", "companies", "business unit", "brand", "manufacturer", "jgh company"],
            "mechanic_details": ["mechanic details", "garage", "vending"],
            "withdrawal_request": ["withdrawal request", "payout request", "tds", "neft"],
            "automatic_transactions": ["automatic transfer", "bank transfer", "imps", "cashfree"],
            "sku_qr_points_map": USER_FRIENDLY_TABLE_ALIASES["sku_qr_points_map"] + ["scanned_boxes", "qr points", "box calculation uom", "box scans", "sku qr points map", "scanned_boxes_retailer", "scanned_boxes_wholesaler"]
        }
        
        for tbl_name, tbl_aliases in aliases.items():
            for alias in tbl_aliases:
                if re.search(rf"\b{alias}\b", q_lower):
                    if tbl_name in self.schema_meta:
                        detected_tables.add(tbl_name)
                        if tbl_name == "role":
                            detected_tables.add("users")
        
        # 1. Match terms via column names & enums
        for tbl_name, tbl_info in self.schema_meta.items():
            cols = tbl_info.get("columns", {})
            col_list = cols.values() if isinstance(cols, dict) else (cols if isinstance(cols, list) else [])
            for col_data in col_list:
                col_name = col_data.get("name", "")
                
                if col_name.lower() not in ["id", "name", "created_at", "updated_at", "status", "type"]:
                    col_words = col_name.replace("_", " ")
                    if len(col_name) > 3 and re.search(rf"\b{col_words}\b", q_lower):
                        detected_tables.add(tbl_name)
                        
                for enum_val in col_data.get("enum_values", []):
                    if re.search(rf"\b{str(enum_val).lower()}\b", q_lower):
                        detected_tables.add(tbl_name)

        # Disambiguation: if retailer/wholesaler/mechanic is asked, remove companies unless explicitly asked
        if "users" in detected_tables and "companies" in detected_tables:
            if not any(k in q_lower for k in ["company", "companies", "brand", "manufacturer", "sap_code", "business unit"]):
                detected_tables.discard("companies")

        # Explicit cross-linking for user wallet transaction queries
        user_terms = ["user", "users", "retailer", "retailers", "dealer", "dealers", "distributor", "distributors", "wholesaler", "wholesalers", "mechanic", "mechanics", "shop owner", "customer", "customers", "name", "mobile", "phone"]
        wallet_terms = ["wallet", "transaction", "transactions", "earning", "earnings", "cashback", "cash point", "balance", "sum", "paid", "topup", "credit", "debit"]
        if any(w in q_lower for w in user_terms) and any(w in q_lower for w in wallet_terms):
            detected_tables.add("users")
            detected_tables.add("wallet_transaction")

        # Match Business Terms from business_dictionary.json
        b_terms = self.business_meta.get("business_terminology", {})
        for term, term_info in b_terms.items():
            term_space = term.replace("_", " ")
            if re.search(rf"\b{re.escape(term_space)}\b", q_lower) or re.search(rf"\b{re.escape(term)}\b", q_lower):
                target_tbl = term_info.get("target_table") or term_info.get("table")
                if target_tbl and target_tbl in self.schema_meta:
                    detected_tables.add(target_tbl)

        # Strict Box Scanning Disambiguation:
        # If question is asking about box scans ("scanned", "scanned boxes", "boxes scanned", "box scan", "box he have scanned", "scanned box"):
        # Map strictly to sku_inventories (si) and sku_qr_points_map. DO NOT route to wallet_transaction.
        box_scan_keywords = ["scanned", "scanned boxes", "boxes scanned", "box scan", "scanned box", "box scans", "boxes", "scan", "scanning"]
        if any(re.search(rf"\b{re.escape(k)}\b", q_lower) for k in box_scan_keywords):
            if not any(k in q_lower for k in ["wallet", "earnings", "earned", "cashback", "cash_point", "credit", "debit", "withdrawal"]):
                detected_tables.discard("wallet_transaction")
                detected_tables.add("sku_inventories")

        # 2. Date Filtering
        m_name, start_date, end_date = self.resolve_date_range(question)
        
        detected_tables_list = list(detected_tables)
        joins = []
        if len(detected_tables_list) > 1:
            for i in range(len(detected_tables_list)):
                for j in range(i + 1, len(detected_tables_list)):
                    path = self.bfs_shortest_path(detected_tables_list[i], detected_tables_list[j])
                    if path:
                        path_joins = self.get_join_clauses_for_path(path)
                        for pj in path_joins:
                            if pj not in joins:
                                joins.append(pj)
                        for t in path:
                            detected_tables.add(t)

        return {
            "question": question,
            "detected_tables": list(detected_tables),
            "date_range": {"start": start_date, "end": end_date} if start_date else None,
            "detected_joins": joins
        }

    def enrich_from_success(self, question: str, sql: str, plan: dict):
        """
        Feedback Loop: When a query succeeds, we learn from it.
        Add the exact structure to our query patterns to avoid LLM hallucinations later.
        """
        # 1. Update Patterns
        pattern_key = question.lower().strip()
        if isinstance(self.query_patterns, dict):
            if "patterns" not in self.query_patterns:
                self.query_patterns["patterns"] = []
            
            # Avoid exact duplicates
            if not any(p.get("question", "").lower() == pattern_key for p in self.query_patterns["patterns"]):
                self.query_patterns["patterns"].append({
                    "question": question,
                    "sql": sql,
                    "tables": plan.get("tables", []) if plan else []
                })
                
                # Async save pattern
                try:
                    with open("knowledge/patterns/query_patterns.json", "w") as f:
                        json.dump(self.query_patterns, f, indent=4)
                except:
                    pass

        # 2. Update Business Terminology (if newly inferred)
        if plan and plan.get("business_terms"):
            updated = False
            if "business_terminology" not in self.business_meta:
                self.business_meta["business_terminology"] = {}
                
            for term_dict in plan["business_terms"]:
                for k, v in term_dict.items():
                    if k not in self.business_meta["business_terminology"]:
                        self.business_meta["business_terminology"][k] = v
                        updated = True
            
            if updated:
                try:
                    with open("knowledge/graph/business_dictionary.json", "w") as f:
                        json.dump(self.business_meta, f, indent=4)
                except:
                    pass

_kg_instance = None
def get_knowledge_graph(reload: bool = False) -> BusinessKnowledgeGraph:
    global _kg_instance
    if _kg_instance is None or reload:
        _kg_instance = BusinessKnowledgeGraph()
    return _kg_instance

def reset_knowledge_graph():
    global _kg_instance
    _kg_instance = BusinessKnowledgeGraph()
    return _kg_instance
