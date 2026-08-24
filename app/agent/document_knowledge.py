"""
Document-Aware Knowledge Base & Entity Intelligence Engine for JGH AI Collaborator.
Loads structured knowledge extracted from:
  1. JGH_Database_Dropdowns_Catalog.pdf -> knowledge/dropdowns_knowledge.json
  2. JGH_Database_Table_Connections_Catalog.pdf -> knowledge/connections_knowledge.json
Provides rich contextual lookups for entities, user roles, table connections, and enum statuses.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

class DocumentKnowledge:
    def __init__(self):
        self.dropdowns_path = KNOWLEDGE_DIR / "dropdowns_knowledge.json"
        self.connections_path = KNOWLEDGE_DIR / "connections_knowledge.json"
        self.dropdowns: Dict[str, Any] = {}
        self.connections: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.dropdowns_path.exists():
            try:
                with open(self.dropdowns_path, "r", encoding="utf-8") as f:
                    self.dropdowns = json.load(f)
            except Exception:
                self.dropdowns = {}

        if self.connections_path.exists():
            try:
                with open(self.connections_path, "r", encoding="utf-8") as f:
                    self.connections = json.load(f)
            except Exception:
                self.connections = {}

    def get_table_dropdowns(self, table_name: str) -> Dict[str, Any]:
        """Returns dropdown and enum configuration for a specific database table."""
        return self.dropdowns.get(table_name.lower().strip(), {})

    def get_table_connections(self, table_name: str) -> Dict[str, Any]:
        """Returns inbound and outbound connection topology for a table."""
        return self.connections.get(table_name.lower().strip(), {})

    def get_role_details(self, role_identifier: str) -> Dict[str, Any]:
        """Looks up specific user role details from the dropdowns catalog."""
        users_dd = self.get_table_dropdowns("users")
        user_role_col = users_dd.get("columns", {}).get("user_role", {})
        values = user_role_col.get("values", {})
        
        target = role_identifier.lower().strip()
        matched = {}
        for k, v in values.items():
            if target in k.lower() or target in v.get("description", "").lower() or target in v.get("use", "").lower():
                matched[k] = v
        return matched

    def explain_entity(self, entity_name: str) -> Optional[str]:
        """
        Generates a rich, document-backed markdown summary for an entity (e.g., 'retailer', 'wholesaler', 'distributor', 'withdrawal').
        """
        ent = entity_name.lower().strip()

        # 1. Retailer
        if ent in ["retailer", "retailers", "mechanic", "mechanics", "dealer", "dealers"]:
            return self._format_retailer_explanation()

        # 2. Wholesaler
        if ent in ["wholesaler", "wholesalers", "stockist", "stockists"]:
            return self._format_wholesaler_explanation()

        # 3. Distributor
        if ent in ["distributor", "distributors"]:
            return self._format_distributor_explanation()

        # 4. Withdrawal / Payout
        if ent in ["withdrawal", "withdrawals", "payout", "payouts", "withdrawal_request"]:
            return self._format_withdrawal_explanation()

        # 5. KYC
        if ent in ["kyc", "kyc_status", "verification", "aadhaar", "pan"]:
            return self._format_kyc_explanation()

        # 6. Specific Table Lookup
        if ent in self.dropdowns or ent in self.connections:
            return self._format_table_explanation(ent)

        return None

    def _format_retailer_explanation(self) -> str:
        users_conn = self.get_table_connections("users")
        inbound_cnt = users_conn.get("inbound_count", 99)

        return f"""### 🎓 Understanding Retailers in the JGH System

In **jghMasterDB**, a **Retailer** represents the core loyalty participant and retail outlet owner who interacts directly with product packaging:

---

#### 1. 🏷️ Identity & User Role
- **Database Identity**: `users.user_role = 2` (*Retailer / Mechanic*)
- **Role in Platform**: Primary retail outlet scanner account. Assigned retailer cash points for scanning product SKU barcodes.
- **Population**: Constitutes **~95.3%** of all registered accounts (27,700+ users).

---

#### 2. 📱 Core Operational Workflow
- **QR Box Scans**: Retailers scan physical packaging barcodes. Each scan logs into `sku_inventories.status_retailer_id` and sets `sku_inventories.retailer_scanned_at`.
- **Points Credit**: Valid scans credit cash points directly to the retailer's wallet ledger in `wallet_transaction` (`reference_type = 'cash_point'`).
- **Target Schemes & Incentives**: Retailers qualify for seasonal volume milestones recorded under `reference_type = 'incentive'`.

---

#### 3. 🔐 Account Status & KYC Lifecycle
From the **Dropdowns Catalog** (`users` table):
- **Account Access (`users.status`)**:
  - `pending`: Self-onboarded via app; scanning and withdrawals are locked until review.
  - `approved`: Fully authorized by admins for scans, schemes, and payouts.
  - `rejected`: Application flagged for invalid profile data or store details.
- **KYC Verification (`users.kyc_status`)**:
  - `0 (Unverified)`: Default on signup; cash withdrawals blocked.
  - `1 (Verified)`: Aadhaar & PAN verified via Digio API; cash payouts enabled.
  - `2 (Rejected)`: Document mismatch; requires re-upload.

---

#### 4. 🔗 Key Database Connections ({inbound_cnt} Connected Tables)
- `sku_inventories.status_retailer_id` ➔ `users.id` *(Scanned box assignment)*
- `wallet_transaction.user_id` ➔ `users.id` *(Point credits, deductions & earnings history)*
- `withdrawal_request.user_id` ➔ `users.id` *(Cash payout requests)*
- `beat_plan_retailers.user_id` ➔ `users.id` *(Sales executive field visit routing)*
- `user_scan_permissions.user_id` ➔ `users.id` *(Fraud detection & scan limits)*

💡 **SQL Querying Tip**: When querying retailer data, always filter by `WHERE u.user_role = 2` and check `u.status = 'approved'`!"""

    def _format_wholesaler_explanation(self) -> str:
        return """### 🎓 Understanding Wholesalers in the JGH System

In **jghMasterDB**, a **Wholesaler** is an intermediate supply chain participant who distributes inventory down to retail outlets:

---

#### 1. 🏷️ Identity & User Role
- **Database Identity**: `users.user_role = 5` (*Wholesaler*)
- **Role in Platform**: Intermediate stockist scanning inbound box inventories before dispatching them to retailers.

---

#### 2. 📦 Dual-Role Box Scanning
- When a wholesaler receives inventory, their scan populates `sku_inventories.status_wholeseller_id` and sets `sku_inventories.wholesaler_scanned_at`.
- Wholesalers receive distinct `wholeseller_cash_points` configured in `sku_qr_points_maps`.
- This dual-scan architecture allows JGH to trace box movement from Distributor ➔ Wholesaler ➔ Retailer.

---

#### 3. 🔗 Key Table Relationships
- `sku_inventories.status_wholeseller_id` ➔ `users.id`
- `wallet_transaction.user_id` ➔ `users.id`
- `users.distributer_id` ➔ Parent distributor's `users.id`

💡 **SQL Querying Tip**: To query wholesaler operations, filter by `WHERE u.user_role = 5`."""

    def _format_distributor_explanation(self) -> str:
        return """### 🎓 Understanding Distributors in the JGH System

In **jghMasterDB**, a **Distributor** manages regional inventory allocations and billing settlements:

---

#### 1. 🏷️ Identity & User Role
- **Database Identity**: `users.user_role = 4` (*Distributor*)
- **Role in Platform**: Primary stock hub managing product distribution lines and financial credit notes.

---

#### 2. 💼 Financial & Settlement Operations
- **Credit Note Settlements**: Distributors settle payments directly with retailers (`credit_notes` table and `wallet_transaction` with `reference_type = 'credit_note'`).
- **Target Tracking**: Monitored via `distributor_targets` mapped to `financial_years`.
- **Team Management**: Oversees regional sales executives and wholesalers via `distributor_teams` and `distributor_wholesaler`.

---

#### 3. 🔗 Key Table Relationships
- `sku_inventories.distributer_id` ➔ `users.id`
- `users.distributer_id` ➔ Links retailers & wholesalers to their parent distributor
- `credit_notes` ➔ Linked to `wallet_transaction_id` for ledger reconciliation

💡 **SQL Querying Tip**: Filter by `WHERE u.user_role = 4` for distributor-level reporting."""

    def _format_withdrawal_explanation(self) -> str:
        return """### 🎓 Understanding the Payout & Withdrawal Workflow

In **jghMasterDB**, cash redemptions are handled across a verified 3-stage pipeline:

---

#### 1. 📝 Stage 1: User Request (`withdrawal_request`)
When a verified user (`kyc_status = 1`) requests a payout:
- **`status`**:
  - `0 (pending)`: Request queued for accountant review on the admin panel.
  - `1 (approved)`: Request authorized; triggers the automated banking payout API.
  - `2 (Reject)`: Request refused (e.g., incorrect bank IFSC). Points refunded to wallet.
- **`withdraw_request_type`**:
  - `bank`: Direct IMPS/NEFT transfer using bank account number and IFSC.
  - `upi`: Instant payout routed to Virtual Payment Address (VPA).

---

#### 2. ⚡ Stage 2: Gateway Execution (`automatic_transactions`)
- Connected to **Cashfree / Razorpay** banking payout API.
- **`status`**:
  - `success`: Funds cleared and confirmed via gateway webhook.
  - `pending`: Payout in transit at the bank.
  - `failed` / `faled`: Gateway transfer rejected (funds returned for retry).
  - `rejected`: Blocked by gateway fraud or risk checks.
- **`transfer_type`**: `IMPS`, `Manual`, `Manual_success`.

---

#### 3. 📒 Stage 3: Immutable Financial Ledger (`wallet_transaction`)
- Successful payouts create a debit record where `reference_type = 'withdrawal'` and `amount < 0`.
- Foreign key links `wallet_transaction.reference_id` ➔ `withdrawal_request.id`.

💡 **SQL Querying Tip**: Total redemptions = `SUM(ABS(amount)) WHERE reference_type = 'withdrawal' AND status = 1`."""

    def _format_kyc_explanation(self) -> str:
        return """### 🎓 Understanding KYC Verification in JGH

From the **JGH Database Dropdowns Catalog** (`users.kyc_status`):

---

#### 1. 🛡️ Status Codes & Business Rules
- **`0 (Unverified)`**: Default state upon mobile app registration. The user can view catalog items but **cannot request cash payouts or withdrawals**.
- **`1 (Verified)`**: Identity verified via Aadhaar OTP and PAN validation (integrated with Digio API). Unlocks the mobile wallet cash withdrawal feature.
- **`2 (Rejected)`**: Document mismatch or invalid PAN format. The user is flagged and prompted to re-upload clear profile credentials.

---

#### 2. 📑 Related Verification Tables
- `digio_kyc_details` (`user_id` ➔ `users.id`): Stores Digio third-party API transaction logs.
- `adhaar_verifications` (`user_id` ➔ `users.id`): Aadhaar OTP verification status log.
- `users.bank_details_status`: `0 = bank data not present`, `1 = bank data present`.

💡 **SQL Querying Tip**: Check verified users with `WHERE u.kyc_status = 1 AND u.bank_details_status = 1`."""

    def _format_table_explanation(self, table_name: str) -> str:
        dd = self.get_table_dropdowns(table_name)
        conn = self.get_table_connections(table_name)

        col_count = dd.get("dropdown_column_count", len(dd.get("columns", {})))
        tot_conn = conn.get("total_connections", 0)
        out_conn = conn.get("outbound_count", 0)
        in_conn = conn.get("inbound_count", 0)

        lines = [f"### 🎓 Database Catalog: `{table_name}` Table Breakdown\n"]
        lines.append(f"**Overview**: `{table_name}` has **{tot_conn} total relationships** ({out_conn} outbound, {in_conn} inbound) and **{col_count} dropdown/enum columns**.\n")

        # Columns
        cols = dd.get("columns", {})
        if cols:
            lines.append("#### 📋 Dropdown & Status Columns:")
            for col_name, col_data in cols.items():
                sql_t = col_data.get("sql_type", "")
                desc = col_data.get("description", "")
                lines.append(f"- **`{col_name}`** (`{sql_t}`): {desc}")
                
                vals = col_data.get("values", {})
                if vals:
                    for vname, vinfo in vals.items():
                        vdesc = vinfo.get("description", "")
                        lines.append(f"  - `{vname}`: {vdesc}")
                elif col_data.get("stored_options"):
                    lines.append(f"  - *Options*: {', '.join(col_data['stored_options'][:8])}")

        # Connections
        outbound = conn.get("outbound", [])
        if outbound:
            lines.append("\n#### ↗️ Outbound Foreign Keys (What this table connects to):")
            for ob in outbound[:6]:
                lines.append(f"- `{table_name}.{ob['column']}` ➔ `{ob['target_table']}.{ob['target_column']}` ({ob['type']})")

        inbound = conn.get("inbound", [])
        if inbound:
            lines.append(f"\n#### ↙️ Inbound References ({len(inbound)} tables reference this table):")
            for ib in inbound[:8]:
                lines.append(f"- `{ib['source_table']}.{ib['source_column']}` ➔ `{table_name}.{ib['referenced_column']}` ({ib['type']})")

        return "\n".join(lines)

document_knowledge = DocumentKnowledge()
