# Walkthrough: CSV Ingestion, RAG Training, and Anti-Hallucination AST Validation

We have completed the integration of the root CSV dumps (`Sku_Inventeries_Dump_data.csv` and `Wallet_Transaction_Dump_Data.csv`) into the Agentic Analyst knowledge layer, updated vector embeddings, fixed AST table alias resolution, updated prompt constraints, and verified execution.

---

## 1. Accomplished Tasks

### CSV Ingestion & Schema Metadata (`app/database/metadata_extractor.py`)
- Created `ingest_csv_dumps()` to read `Sku_Inventeries_Dump_data.csv` and `Wallet_Transaction_Dump_Data.csv` directly from project root.
- Ingested column definitions, data types, and distinct categorical values for `transaction_type` (`cash_point`, `referral_earning`, `topup`, `coupon_redeem`).
- Merged schema definitions and enums into `knowledge/schema/schema_metadata.json` and `knowledge/schema/enum_dictionary.json`.

### ChromaDB RAG Vector Store Re-indexing (`app/embedding/chroma_builder.py`)
- Completed `build_embeddings()` and `rebuild_embeddings()` functions in `app/embedding/chroma_builder.py`.
- Successfully generated DDL cards and embedded 9 target enterprise tables into ChromaDB collection `enterprise_schema`.

### Business Dictionary & Relationship Mapping (`knowledge/graph/business_dictionary.json`)
- Mapped `"retailer"` and `"retailers"` to `users.user_role = 2`.
- Mapped `"monthly earnings"` and `"retailer earnings"` to `wallet_transaction`:
  - Filter: `wallet_transaction.transaction_type IN ('cash_point', 'referral_earning', 'topup', 'coupon_redeem')`.
  - Date Scope: `wallet_transaction.created_at >= DATE_FORMAT(NOW(), '%Y-%m-01')`.
  - Conditional Aggregation for `cash_point_earning`, `referral_earning`, `topup_earning`, `coupon_redeem_earning`, and `total_monthly_earning`.

### Prompt Constraints & Anti-Hallucination (`app/prompt/prompt_builder.py`)
- Appended strict anti-hallucination rules to `build_sql_prompt()`:
  - Prohibited inventing non-existent columns (`transaction_count`, `total_invoiced_quantity`).
  - Mandated `COUNT(*)` or `COUNT(primary_key)` for row counting.
  - Enforced column matching with `schema_metadata.json`.

### AST Validator & Self-Correction Loop (`app/validator/sql_ast_validator.py`, `app/agent/sql_agent.py`)
- Implemented AST table alias mapping (`alias_to_table`) so aliases like `wt` -> `wallet_transaction` and `u` -> `users` resolve to actual table names.
- Checked all referenced columns against `table_to_cols[real_table]`.
- Raised explicit `SQLValidationError("Column '<col_name>' does not exist in table '<table_name>'")` when invalid columns are generated, passing explicit feedback into the LLM retry prompt.

---

## 2. Verification Results

### Test Execution (`test_retailer_earnings.py`)
- Executed query for: `"who all are retailers available in the users table, for those retailers how much they all are earning in this month: cash_point, referral earning, topup, coupon_redeem"`

```sql
SELECT 
    users.id,
    users.name,
    users.last_name,
    SUM(CASE WHEN wallet_transaction.transaction_type = 'cash_point' THEN wallet_transaction.amount ELSE 0 END) AS cash_point,
    SUM(CASE WHEN wallet_transaction.transaction_type = 'referral_earning' THEN wallet_transaction.amount ELSE 0 END) AS referral_earning,
    SUM(CASE WHEN wallet_transaction.transaction_type = 'topup' THEN wallet_transaction.amount ELSE 0 END) AS topup,
    SUM(CASE WHEN wallet_transaction.transaction_type = 'coupon_redeem' THEN wallet_transaction.amount ELSE 0 END) AS coupon_redeem
FROM 
    users
JOIN 
    wallet_transaction ON users.id = wallet_transaction.user_id
WHERE 
    users.user_role = 2
    AND wallet_transaction.created_at BETWEEN '2026-08-01' AND '2026-09-01'
GROUP BY 
    users.id;
```

**Results:**
- **Status:** `success`
- **Validation:** 0 column errors (AST validation passed)
- **Execution Success:** `True`
- **Rows Returned:** 500 rows
- **Sample Record:** `{'id': 65410, 'name': 'RADHA RAMAN', 'last_name': None, 'cash_point': 0.0, 'referral_earning': 0.0, 'topup': 0.0, 'coupon_redeem': 0.0}`
