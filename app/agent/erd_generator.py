"""
ERD & Visual Architecture Generator Agent for JGH AI Collaborator.
Handles ERD_GEN intent mode:
  - Generates valid Mermaid.js markup (erDiagram ...) for requested tables
    or the core 8 target tables using relationship graph mappings.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

class ERDGenerator:
    def __init__(self):
        self.graph_path = KNOWLEDGE_DIR / "draft_relationship_graph.json"
        self._load_graph()

    def _load_graph(self):
        self.edges = []
        if self.graph_path.exists():
            try:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.edges = data.get("candidate_edges", [])
            except Exception:
                pass

    def generate_diagram(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower()

        # Identify requested target tables
        core_scope = [
            "users", "wallet_transaction", "sku_inventories",
            "sku_qr_points_maps", "withdrawal_request",
            "automatic_transactions", "companies"
        ]

        requested_tables = [t for t in core_scope if t in p_lower or t[:-1] in p_lower]
        if not requested_tables:
            requested_tables = core_scope

        mermaid_str = self._build_mermaid_code(requested_tables)

        explanation = (
            "### 📐 Visual Architecture & ER Diagram\n\n"
            "Below is the interactive Mermaid.js Entity-Relationship diagram for the requested database tables, "
            "showing primary keys, foreign keys, and dual-role scan relationships:\n\n"
            "```mermaid\n"
            f"{mermaid_str}\n"
            "```\n\n"
            "💡 **Relationship Key**:\n"
            "- `users` ↔ `wallet_transaction`: Direct user ledger link (`user_id`)\n"
            "- `users` ↔ `sku_inventories`: Dual-role scan links (`status_retailer_id` & `status_wholeseller_id`)\n"
            "- `sku_inventories` ↔ `sku_qr_points_maps`: UOM & cash points lookup (`sku_code`)"
        )

        return {
            "mode": "ERD_GEN",
            "requested_tables": requested_tables,
            "mermaid_code": mermaid_str,
            "response": explanation,
            "sql_executed": False
        }

    def _build_mermaid_code(self, target_tables: List[str]) -> str:
        lines = ["erDiagram"]

        # Table definitions with key columns
        table_defs = {
            "users": """    users {
        bigint id PK
        varchar user_role
        varchar mobile_number
        bigint wallet_balance
        timestamp created_at
    }""",
            "wallet_transaction": """    wallet_transaction {
        bigint id PK
        bigint user_id FK
        decimal amount
        varchar reference_type
        tinyint status
        timestamp created_at
    }""",
            "sku_inventories": """    sku_inventories {
        bigint id PK
        varchar sku_code FK
        bigint status_retailer_id FK
        bigint status_wholeseller_id FK
        bigint distributer_id FK
        varchar order_type
        timestamp retailer_scanned_at
        timestamp wholeseller_scanned_at
    }""",
            "sku_qr_points_maps": """    sku_qr_points_maps {
        bigint id PK
        varchar sku_code
        varchar uom
        varchar gride_type
        decimal retailer_cash_points
        decimal wholeseller_cash_points
    }""",
            "withdrawal_request": """    withdrawal_request {
        bigint id PK
        bigint user_id FK
        int amount
        bigint automatic_transaction_id FK
        tinyint status
        timestamp created_at
    }""",
            "automatic_transactions": """    automatic_transactions {
        bigint id PK
        bigint user_id FK
        varchar transaction_id
        varchar transfer_type
        double amount
    }""",
            "companies": """    companies {
        bigint id PK
        bigint business_info_id
        varchar name
        varchar business_unit
    }"""
        }

        # Add target table definitions
        for tbl in target_tables:
            if tbl in table_defs:
                lines.append(table_defs[tbl])

        # Add relationship edges
        relationships = [
            '    users ||--o{ wallet_transaction : "user_id"',
            '    users ||--o{ sku_inventories : "status_retailer_id (Retailer)"',
            '    users ||--o{ sku_inventories : "status_wholeseller_id (Wholesaler)"',
            '    users ||--o{ sku_inventories : "distributer_id (Distributor)"',
            '    sku_inventories ||--o{ sku_qr_points_maps : "sku_code"',
            '    users ||--o{ withdrawal_request : "user_id"',
            '    withdrawal_request ||--o{ automatic_transactions : "automatic_transaction_id"',
            '    companies ||--o{ users : "business_info_id"'
        ]

        lines.extend(relationships)
        return "\n".join(lines)

erd_generator = ERDGenerator()
