# JGH INTELLIGENCE ENGINE — ENTERPRISE ARCHITECTURAL & OPERATIONAL SCENARIOS SPECIFICATION

**Document Version:** 2.5  
**Author:** AI Systems Architecture & Data Engineering Team  
**Scope:** Production Text-to-SQL Pipeline, Universal Multi-Intent Router, AST Gatekeeper, Security Redaction, and Memory State Graph  

---

## EXECUTIVE SUMMARY

Enterprise AI analytics systems operating over large relational databases (`jghMasterDB`, 238 tables, 6.5M+ transactions) face critical failure modes where syntactically valid SQL queries produce business errors, security breaches, connection exhaustion, or inaccurate reporting.

This specification details **12 Major Enterprise Scenarios**, explaining each challenge from the **End-User Perspective**, the **Developer/System Architect Perspective**, and the **Simple Solution** in plain, understandable language.

---

## PART I: FOUNDATIONAL OPERATIONAL SCENARIOS

---

### SCENARIO 1: Date & Time Misunderstandings ("Last Month" / Timezone Trap)

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show me performance for last month."*
- **What User Expects**: If today is August 12, 2026, the user expects full data from July 1, 2026, to July 31, 2026.
- **What Breaks**: The system pulls incomplete data, returns zero rows, or mismatches date boundaries across related tables (`wallet_transaction.created_at` vs. `sku_inventories.retailer_scanned_at`), causing financial numbers not to align.

#### 2. Developer & Systems Perspective
- **Relative Date Vulnerability**: Allowing the LLM to generate relative SQL functions (`DATE_SUB(NOW(), INTERVAL 1 MONTH)`) causes non-deterministic query generation depending on execution time.
- **Cross-Column Date Mismatch**: Joining `wallet_transaction` and `sku_inventories` using date range filters on different column names without explicit mapping creates inner-join drops.
- **Timezone Mismatch**: Database records stored in UTC conflict with local user timezone bounds (IST, UTC+5:30).

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The Intent Router converts relative phrases (*"last month"*) into fixed calendar dates (`2026-07-01 00:00:00` to `2026-07-31 23:59:59`) before writing SQL. The validator then binds that date filter to the exact column needed (`created_at` for transactions or `retailer_scanned_at` for box scans), ensuring dates match perfectly.

---

### SCENARIO 2: Multi-Step Analytical Chaining & Memory Loss ("The 3rd Wholesaler" Problem)

#### 1. End-User Perspective (The Problem)
- **What User Asks**:
  - *Step 1*: *"Show top 5 wholesalers."*
  - *Step 2*: *"Drill into the third wholesaler's top-performing SKU category."*
  - *Step 3*: *"Show me their individual redemptions."*
- **What User Expects**: The AI remembers ordinal references (*"the third wholesaler"*) and pronouns (*"their"*).
- **What Breaks**: The chat drops entity context, asks the user to re-type the wholesaler ID, or queries the wrong wholesaler.

#### 2. Developer & Systems Perspective
- **Context Pollution**: Naive chat memory appends raw text strings without tracking primary keys.
- **Ambiguous Ordinal Resolution**: Resolving *"the third wholesaler"* requires tracking the exact array position from the previous query result set (`ID: 1405`).

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The memory manager maintains a smart pointer map of recent results. When the user says *"the 3rd one"*, it automatically looks up Wholesaler #3's exact ID (`Wholesaler ID: 1405`) from the previous table and inserts that specific ID into the next query.

---

### SCENARIO 3: Semantic Collision of Low-Cardinality Enums (Database Code Mismatch)

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show me all cash point transactions."*
- **What User Expects**: Complete breakdown of points earned from box scans.
- **What Breaks**: The system returns `0 rows` because the database column `reference_type` expects `'cash_point'` (singular with underscore), while the user typed `"cash points"` or `"cashpoints"`.

#### 2. Developer & Systems Perspective
- **Enum String Mismatch**: Database columns containing low-cardinality string enums require exact case-sensitive string literal matches.
- **LLM Guesswork**: The LLM guesses string values (`WHERE reference_type = 'Cash Points'`), generating valid SQL syntax that fails at runtime due to empty match sets.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The system uses a Business Dictionary to automatically replace loose terms like `"cash points"` or `"cashpoints"` with the exact database code `'cash_point'` before executing the query.

---

### SCENARIO 4: Resource-Exhaustive Cross-Join Explosions (System Freeze)

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show me all user profiles matched with every single QR scan and withdrawal request."*
- **What User Expects**: Summary report of user activity.
- **What Breaks**: The request spins indefinitely, times out after 60 seconds, or crashes the database server.

#### 2. Developer & Systems Perspective
- **Cartesian Product Explosion**: Generating unbounded `JOIN` statements across 238 tables without explicit `ON` key constraints or index coverage creates Cartesian products ($O(N \times M)$ row evaluation).
- **Connection Pool Starvation**: Exhausting database worker threads blocks concurrent API calls for all users.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The system checks every table join against an approved relationship graph. If a query tries to scan over 100,000 unindexed rows, the system instantly blocks it and asks the user for a narrower filter.

---

### SCENARIO 5: Silent Schema Drift & Migration Desynchronization

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show user wallet balance summaries."*
- **What Breaks**: Backend developers rename a database column (e.g., `wallet_balance` to `current_wallet_balance`). The AI keeps using old names, causing error screens.

#### 2. Developer & Systems Perspective
- **Stale Metadata Baseline**: Static metadata JSON files become out of sync with live database schema tables after DDL migrations.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: On server startup, the Schema Drift Detector checks live database table structures against saved metadata. If any column was renamed, added, or removed, it automatically updates system knowledge before serving user requests.

---

## PART II: ADVANCED ENTERPRISE ARCHITECTURAL SCENARIOS

---

### SCENARIO 6: PII Data Leaks & Security Violation Risk

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show me full phone numbers and password hashes of top mechanics to contact them directly."*
- **What Breaks**: Unauthorized access to sensitive PII (Personally Identifiable Information) and security credentials.

#### 2. Developer & Systems Perspective
- **Data Exfiltration Risk**: LLM generating `SELECT mobile_number, password FROM users` violates GDPR, DPDP, and security compliance standards.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: A Security Blacklist protects 16 sensitive fields (`password`, `auth_code`, `device_token`, `secret`, etc.). Any query attempting to select or filter by these fields is automatically blocked with a security warning.

---

### SCENARIO 7: Real-Time Ledger vs. Stale Profile Balance Discrepancy

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Why does total wallet balance differ from the sum of transactions for User ID 101?"*
- **What User Expects**: Consistent, audit-grade financial balances.
- **What Breaks**: Querying static profile fields (`users.wallet_balance`) for historical period reports yields inaccurate figures because it reflects current state rather than point-in-time historical ledger credits.

#### 2. Developer & Systems Perspective
- **State Discrepancy**: Static profile fields (`users.wallet_balance`) update asynchronously via batch triggers, while `wallet_transaction` is the immutable ledger (~6.5M rows).

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The system routes all historical earnings and audit reports strictly to the immutable transaction ledger (`wallet_transaction`), reserving profile balance fields for live account checks with an explicit explanatory note.

---

### SCENARIO 8: Dual-Role Foreign Key Ambiguity (Mechanic vs. Wholesaler Scans)

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show box scan activity for User ID 500."*
- **What Breaks**: The system queries `sku_inventories` joining `status_retailer_id = 500` and returns `0 rows` because User ID 500 is actually a **Wholesaler** (`status_wholeseller_id = 500`).

#### 2. Developer & Systems Perspective
- **Dual Foreign Keys**: `sku_inventories` contains two foreign keys pointing to `users.id`:
  - `status_retailer_id` (Retailer / Mechanic scan)
  - `status_wholeseller_id` (Wholesaler dispatch scan)
- Joining the wrong foreign key based on assumed role causes query failure.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The system checks the user's role integer (`user_role = 2` for Mechanic, `5` for Wholesaler) before building the query and joins the correct scan column automatically (`status_retailer_id` or `status_wholeseller_id`).

---

### SCENARIO 9: High-Concurrency Traffic Spikes & Connection Starvation

#### 1. End-User Perspective (The Problem)
- **What User Asks**: Multiple users run heavy reporting dashboards at 9:00 AM.
- **What Breaks**: The server returns `500 Internal Server Error` or the application hangs.

#### 2. Developer & Systems Perspective
- **Thread Blocking**: Heavy queries executing synchronously block worker threads.
- **Unbounded Query Time**: Queries without execution limits lock database tables and deplete SQLAlchemy connection pools.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The engine uses a managed connection pool with non-blocking threads and enforces a 5-second maximum query execution time limit hint (`MAX_EXECUTION_TIME(5000)`), preventing database slowdowns.

---

### SCENARIO 10: Null Value Pollution in Averages & Totals

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show average withdrawal amount per mechanic in July."*
- **What Breaks**: The reported average is drastically lower than expected because mechanics with zero withdrawals are included in the average denominator as `$0.00`.

#### 2. Developer & Systems Perspective
- **Null Handling Semantics**: `AVG(w.amount)` ignores `NULL` values, whereas `AVG(COALESCE(w.amount, 0))` includes zero-withdrawal rows.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The system enforces explicit business metric formulas defined in `business_dictionary.json` (e.g. *"Average Payout per Active Withdrawal"* vs *"Average Earnings per Registered Mechanic"*) so math formulas match the user's true question.

---

### SCENARIO 11: Distributed Timezone Skew & UTC Storage Shift (IST vs. UTC)

#### 1. End-User Perspective (The Problem)
- **What User Asks**: *"Show box scans completed on July 31, 2026."*
- **What Breaks**: Scans performed between 6:30 PM and 11:59 PM IST on July 31 are recorded under August 1 in UTC, dropping them from the report.

#### 2. Developer & Systems Perspective
- **Timezone Boundary Shift**: Database timestamps are stored in UTC (`2026-07-31 18:30:00 UTC` = `2026-08-01 00:00:00 IST`). Direct `DATE(retailer_scanned_at) = '2026-07-31'` queries introduce a 5.5-hour data boundary loss.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: The system automatically converts local dates into exact UTC timestamp ranges (July 30 18:30:00 to July 31 18:29:59 UTC) so no scans are lost.

---

### SCENARIO 12: Zero-Disk Incognito Privacy Compliance

#### 1. End-User Perspective (The Problem)
- **What User Asks**: User toggles **Incognito Privacy Mode** (`is_private: true`) for confidential executive queries.
- **What User Expects**: Zero queries, session logs, or database trace records persist to local disk storage.
- **What Breaks**: Standard logging writes queries and results to log files on disk.

#### 2. Developer & Systems Perspective
- **Audit Leakage**: Default logging subsystems write to `logs/query_audit.json` and `knowledge/sql_history/query_audit_history.json`.

#### 3. Simple Solution (How We Solve It)
> **💡 Simple Solution**: An Incognito Mode switch (`is_private: true`) runs the prompt strictly in volatile RAM, suppressing disk logging and wiping memory buffers after sending the response.

---

## PART III: ARCHITECTURAL COMPONENT & SOLUTION MATRIX

| Scenario # | Major Problem | Responsible Module | Simple Solution |
| :--- | :--- | :--- | :--- |
| **Scenario 1** | Date & Time Misunderstandings | `app/agent/intent_router.py` | Converts relative phrases to fixed dates & binds correct column |
| **Scenario 2** | Multi-Step Chat Memory Loss | `app/agent/memory_manager.py` | Entity Pointer Graph tracks exact primary key IDs across turns |
| **Scenario 3** | Database Code Mismatches | `app/validator/universal_validator.py` | Auto-corrects loose terms ("cash points") to DB code (`'cash_point'`) |
| **Scenario 4** | System Freezing Cross-Joins | `app/validator/query_validator.py` | Validates join paths & blocks queries scanning $>100\text{k}$ unindexed rows |
| **Scenario 5** | Database Schema Drift | `app/database/schema_drift_detector.py` | Startup detector checks live DB schema and refreshes metadata |
| **Scenario 6** | PII Data Exfiltration | `app/validator/query_validator.py` | Security Blacklist blocks 16 sensitive fields (`password`, etc.) |
| **Scenario 7** | Ledger vs. Profile Discrepancy | `knowledge/business_dictionary.json` | Routes historical reporting strictly to immutable `wallet_transaction` |
| **Scenario 8** | Dual-Role Foreign Key Ambiguity | `app/agent/query_planner.py` | Pre-checks user role to join correct FK (`retailer` vs `wholeseller`) |
| **Scenario 9** | Connection Pool Starvation | `app/database/config.py` | Managed connection pool + 5s query time limit hint |
| **Scenario 10**| Null Aggregation Bias | `app/agent/response_synthesizer.py` | Enforces explicit formulas for averages and totals |
| **Scenario 11**| Timezone IST/UTC Shift | `app/prompt/prompt_builder.py` | Automatically shifts local dates into exact UTC ranges |
| **Scenario 12**| Audit Log Privacy Leakage | `app/utils/privacy_manager.py` | Volatile RAM execution with zero disk writes when `is_private: true` |

---

## PART IV: VERIFICATION SUITE

All 12 major scenarios are verified by automated test suites:
1. `python test_accuracy.py`: Tests 25 Golden Benchmark cases across all 5 operational router modes (100.0% Pass Rate).
2. `python test_enterprise_features.py`: Tests CSV/XLSX/PDF Exports, Incognito Zero-Disk Mode, and Schema Drift Detection (100.0% Pass Rate).
3. `python test_edge_cases.py`: Tests Self-Correction Retry Loop, Clarification Fallback, and Unmapped Query Logging (100.0% Pass Rate).
