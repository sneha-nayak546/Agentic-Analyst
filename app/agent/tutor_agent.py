"""
Database Tutor & Onboarding Coach Agent for JGH AI Collaborator.
Handles TUTOR_QA intent mode:
  - Explains schema concepts, user roles (Retailer Role 2, Wholesaler Role 5, Distributor Role 4),
    business terms, table relationships, and KYC/ledger rules in warm, friendly plain English
    backed by the JGH Database Dropdowns Catalog and Table Connections Catalog.
"""

import json
from pathlib import Path
from typing import Dict, Any
from app.agent.document_knowledge import document_knowledge

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

class TutorAgent:
    def __init__(self):
        self.dictionary_path = KNOWLEDGE_DIR / "business_dictionary.json"
        self.schema_path = KNOWLEDGE_DIR / "schema" / "draft_schema_metadata.json"
        self.doc_knowledge = document_knowledge
        self._load_knowledge()

    def _load_knowledge(self):
        self.dict_data = {}
        self.schema_data = {}
        if self.dictionary_path.exists():
            try:
                with open(self.dictionary_path, "r", encoding="utf-8") as f:
                    self.dict_data = json.load(f)
            except Exception:
                pass
        if self.schema_path.exists():
            try:
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    self.schema_data = json.load(f)
            except Exception:
                pass

    def explain(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower().strip()

        # 1. Retailer Entity
        if any(w in p_lower for w in ["retailer", "retailers", "shop owner", "shopkeeper", "dealer", "mechanic"]):
            explanation = self.doc_knowledge.explain_entity("retailer")
            return {
                "mode": "TUTOR_QA",
                "topic": "Retailer & Mechanic Ecosystem",
                "response": explanation,
                "sql_executed": False
            }

        # 2. Wholesaler Entity
        if any(w in p_lower for w in ["wholesaler", "wholesalers", "stockist", "stockists"]):
            explanation = self.doc_knowledge.explain_entity("wholesaler")
            return {
                "mode": "TUTOR_QA",
                "topic": "Wholesaler Supply Chain",
                "response": explanation,
                "sql_executed": False
            }

        # 3. Distributor Entity
        if any(w in p_lower for w in ["distributor", "distributors"]):
            explanation = self.doc_knowledge.explain_entity("distributor")
            return {
                "mode": "TUTOR_QA",
                "topic": "Distributor Operations",
                "response": explanation,
                "sql_executed": False
            }

        # 4. Withdrawal / Payout Workflow
        if any(w in p_lower for w in ["withdrawal", "withdrawals", "payout", "payouts", "payout request"]):
            explanation = self.doc_knowledge.explain_entity("withdrawal")
            return {
                "mode": "TUTOR_QA",
                "topic": "Payout & Withdrawal Workflow",
                "response": explanation,
                "sql_executed": False
            }

        # 5. KYC & Verification
        if any(w in p_lower for w in ["kyc", "kyc_status", "aadhaar", "pan", "verification", "verified"]):
            explanation = self.doc_knowledge.explain_entity("kyc")
            return {
                "mode": "TUTOR_QA",
                "topic": "User KYC Verification",
                "response": explanation,
                "sql_executed": False
            }

        # 6. User Roles Taxonomy
        if "role" in p_lower or "user_role" in p_lower:
            return self._explain_user_roles()

        # 7. Earnings vs Redemptions / Reference Types
        if any(w in p_lower for w in ["earning", "earnings", "redemption", "redemptions", "reference_type", "cash_point", "topup"]):
            return self._explain_earnings_and_redemptions()

        # 8. Wallet Balances & Ledgers
        if "balance" in p_lower or "ledger" in p_lower:
            return self._explain_balances()

        # 9. Box Scans & SKU Movement
        if any(w in p_lower for w in ["scan", "scans", "sku", "box", "inventory"]):
            return self._explain_inventory_scans()

        # 10. Specific Table Search from Document Knowledge
        for tbl in self.doc_knowledge.dropdowns.keys():
            if tbl in p_lower:
                explanation = self.doc_knowledge.explain_entity(tbl)
                if explanation:
                    return {
                        "mode": "TUTOR_QA",
                        "topic": f"Table: {tbl}",
                        "response": explanation,
                        "sql_executed": False
                    }

        # 11. General Schema Overview with Enhanced Context
        return self._explain_general_schema(prompt)

    def _explain_user_roles(self) -> Dict[str, Any]:
        roles_text = """### 🎓 Database Tutor: User Role Taxonomy Explanation

Welcome to the **JGH System User Role Guide**! In `jghMasterDB`, user accounts are categorized using the `user_role` integer column in the `users` table:

1. **Role 2 — Retailers / Mechanics / End Users** *(95.3% of Users - 27,703 Accounts)*: Primary loyalty participants who scan SKU QR codes on product boxes to earn cash and bonus points.
2. **Role 4 — Distributor Partners** *(1.57% - 457 Accounts)*: Supply chain distributors managing regional product allocations, target tracking, and credit note settlements.
3. **Role 5 — Wholesalers / Stockists** *(1.97% - 573 Accounts)*: Intermediate stockists who order box inventories and distribute them down to retailers with dual-role scan tracking.
4. **Role 1 — Business Admins**: Company-level administrators managing regional SKU mappings and campaign schemes.
5. **Role 6 — Super Admins**: Top-tier corporate administration with full platform and KYC governance.
6. **Role 7 & 8 — Area & State Heads**: Regional and state operational leaders.
7. **Role 10 — Warehouse Managers**: Primary logistics and dispatch heads at the Kolkata distribution center.
8. **Role 13 — Accounts Head**: Financial controllers managing withdrawal approvals and automated bank payouts.

💡 **Key Takeaway**: When querying user activity or earnings, **Role 2** represents your core retail earners, while **Roles 4 and 5** represent supply chain distributors and stockists!"""

        return {
            "mode": "TUTOR_QA",
            "topic": "User Role Taxonomy",
            "response": roles_text,
            "sql_executed": False
        }

    def _explain_earnings_and_redemptions(self) -> Dict[str, Any]:
        text_body = """### 🎓 Database Tutor: Earnings vs. Redemptions

In `jghMasterDB`, all monetary movements are recorded in the `wallet_transaction` ledger under the `reference_type` column (extracted from the **Dropdowns Catalog**):

#### 1. 💰 Earnings (Monetary Credits)
- **`cash_point`**: Points earned by scanning QR codes on product boxes (**>97% of total transactions**).
- **`topup`**: Direct wallet balance credits or manual admin adjustments.
- **`incentive`**: Performance-based campaign bonuses awarded for quarterly scan milestones.
- **`bonus_conversion`**: Points converted from promotional gift points into wallet cash balance.
- **`referral_earning`**: Bonus credits awarded for onboarding new mechanics or retailers.
- **`credit_note`**: Distributor accounting adjustments for returned or settled inventories.

#### 2. 🏦 Redemptions (Cash Payouts)
- **`withdrawal`**: Money withdrawn by users into verified bank accounts or UPI VPAs via automated gateway payouts (`automatic_transactions`).

💡 **Rule**: To calculate total money earned, sum transactions where `reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning')`. To calculate payouts, sum where `reference_type = 'withdrawal'`."""

        return {
            "mode": "TUTOR_QA",
            "topic": "Earnings vs Redemptions",
            "response": text_body,
            "sql_executed": False
        }

    def _explain_balances(self) -> Dict[str, Any]:
        text_body = """### 🎓 Database Tutor: Static Profile Balance vs. Dynamic Ledger Balance

There are two ways wallet balances exist in `jghMasterDB`:

1. **Static Profile Snapshot (`users.wallet_balance`)**:
   - Stored directly on the user's profile record in the `users` table.
   - Quick lookup for instant UI display in the mobile app.

2. **Dynamic Ledger Balance (`SUM(wallet_transaction.amount)`)**:
   - Calculated by summing all historical transactions in `wallet_transaction`:
     `SUM(CASE WHEN reference_type IN ('cash_point', 'topup', 'redeem_coupon', 'incentive', 'bonus_conversion', 'referral_earning') THEN amount ELSE -amount END)`
   - Serves as the immutable financial audit trail.

💡 **Recommendation**: For point-in-time financial reporting, always use the dynamic ledger balance to guarantee accounting accuracy!"""

        return {
            "mode": "TUTOR_QA",
            "topic": "Wallet Balances",
            "response": text_body,
            "sql_executed": False
        }

    def _explain_inventory_scans(self) -> Dict[str, Any]:
        text_body = """### 🎓 Database Tutor: Dual-Role Box Scans & Inventory Velocity

In `jghMasterDB`, product packaging lifecycle is tracked through `sku_inventories`:

1. **Dual-Role Scan Tracking**:
   - **Wholesaler Scan**: Populates `status_wholeseller_id` (`users.id`) and sets timestamp `wholesaler_scanned_at`.
   - **Retailer Scan**: Populates `status_retailer_id` (`users.id`) and sets timestamp `retailer_scanned_at`.
2. **Points Configuration**:
   - `sku_inventories.sku_code` connects to `sku_qr_points_maps.sku_code` to calculate unit points (`retailer_cash_points` and `wholeseller_cash_points`).
3. **Dispatch Origins**:
   - Sourced primarily from `tirupur` and `kolkata` distribution centers (`sku_inventories.sources`).

💡 **Insight**: Always query `sku_inventories` for physical box counts and velocity metrics!"""

        return {
            "mode": "TUTOR_QA",
            "topic": "Dual-Role Inventory Scans",
            "response": text_body,
            "sql_executed": False
        }

    def _explain_general_schema(self, prompt: str) -> Dict[str, Any]:
        text_body = f"""### 🎓 Database Tutor: JGH Intelligence Knowledge Base

You asked: *"{prompt}"*

The **jghMasterDB** database contains **238 tables** with over **192 documented dropdown and status attributes**:

- **Core User Accounts (`users`)**: 104 connected tables, manages `user_role` (Retailer 2, Wholesaler 5, Distributor 4), `kyc_status` (Aadhaar/PAN via Digio), and account approval states.
- **Financial Ledger (`wallet_transaction`)**: Over 6.5M records tracking `cash_point`, `topup`, `incentive`, and `withdrawal`.
- **Inventory Box Scans (`sku_inventories`)**: Dual-role scan tracking across wholesalers (`wholesaler_scanned_at`) and retailers (`retailer_scanned_at`).
- **Payout Pipeline (`withdrawal_request` & `automatic_transactions`)**: Automated Cashfree/Razorpay bank and UPI transfer workflows.

Feel free to ask specific questions like:
- *"Explain about retailer"*
- *"Explain about withdrawal workflow"*
- *"What are the KYC status codes?"*
- *"How does dual-role box scanning work?"*"""

        return {
            "mode": "TUTOR_QA",
            "topic": "General Schema",
            "response": text_body,
            "sql_executed": False
        }

tutor_agent = TutorAgent()
