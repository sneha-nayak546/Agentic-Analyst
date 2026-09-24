# JGH Intelligence NL2SQL Accuracy Engineering Report — live_run
**Generated:** 2026-09-23T09:36:36Z | **Total Questions:** 30

## 1. Executive Metrics

| Metric | Score | Target | Status |
|---|---|---|---|
| **End-to-End Accuracy** | **43.3%** | ≥ 90.0% | ⚠️ ITERATION REQUIRED |
| Intent Detection Accuracy | 96.7% | ≥ 95.0% | ✅ |
| Schema Retrieval Accuracy | 100.0% | ≥ 95.0% | ✅ |
| SQL Semantic Accuracy | 93.3% | ≥ 92.0% | ✅ |
| SQL Execution Success | 100.0% | ≥ 98.0% | ✅ |
| Database Result Accuracy | 66.7% | ≥ 92.0% | ⚠️ |
| Final Response Accuracy | 73.3% | ≥ 92.0% | ⚠️ |
| P50 Latency | 7946ms | < 3000ms | ⚠️ |
| P95 Latency | 120761ms | < 8000ms | ⚠️ |

## 2. Accuracy by Difficulty

| Difficulty | Total | Passed | Accuracy |
|---|---|---|---|
| EASY | 3 | 3 | 100.0% |
| MEDIUM | 16 | 7 | 43.8% |
| HARD | 11 | 3 | 27.3% |

## 3. Accuracy by Business Category (30 Categories)

| Category | Total | Passed | Accuracy | Status |
|---|---|---|---|---|
| Adversarial Questions | 1 | 1 | 100.0% | ✅ |
| Aggregation | 1 | 1 | 100.0% | ✅ |
| Ambiguous Natural Language | 1 | 0 | 0.0% | 🔴 |
| Bottom N | 1 | 1 | 100.0% | ✅ |
| Comparisons | 1 | 0 | 0.0% | 🔴 |
| Complex Multi Condition | 1 | 0 | 0.0% | 🔴 |
| Context Dependent | 1 | 0 | 0.0% | 🔴 |
| Context Independent | 1 | 0 | 0.0% | 🔴 |
| Counting | 1 | 1 | 100.0% | ✅ |
| Date Time | 1 | 0 | 0.0% | 🔴 |
| Distinct Counting | 1 | 1 | 100.0% | ✅ |
| Edge Cases | 1 | 0 | 0.0% | 🔴 |
| Fewer Than Requested | 1 | 0 | 0.0% | 🔴 |
| Filtering | 1 | 1 | 100.0% | ✅ |
| Follow Up Questions | 1 | 0 | 0.0% | 🔴 |
| Grouping | 1 | 1 | 100.0% | ✅ |
| Joins | 1 | 0 | 0.0% | 🔴 |
| Multi Table | 1 | 0 | 0.0% | 🔴 |
| Multiple Filters | 1 | 1 | 100.0% | ✅ |
| Negative Values | 1 | 0 | 0.0% | 🔴 |
| Null Handling | 1 | 0 | 0.0% | 🔴 |
| Paraphrased Questions | 1 | 0 | 0.0% | 🔴 |
| Percentage Calculations | 1 | 0 | 0.0% | 🔴 |
| Ranking | 1 | 1 | 100.0% | ✅ |
| Simple Lookup | 1 | 1 | 100.0% | ✅ |
| Synonyms | 1 | 0 | 0.0% | 🔴 |
| Time Comparisons | 1 | 1 | 100.0% | ✅ |
| Top N | 1 | 0 | 0.0% | 🔴 |
| Trend Questions | 1 | 1 | 100.0% | ✅ |
| Zero Result Queries | 1 | 1 | 100.0% | ✅ |

## 4. Failure Taxonomy & Root Cause Breakdown

| Failure Category | Count | Primary Impact |
|---|---|---|
| `WRONG_FINAL_RESPONSE` | 8 | Requires general pipeline hardening |
| `WRONG_DATABASE_RESULT` | 7 | Requires general pipeline hardening |
| `WRONG_INTENT` | 1 | Requires general pipeline hardening |
| `WRONG_LIMIT` | 1 | Requires general pipeline hardening |

## 5. Sample Failed Queries & Diagnoses

### Question #17: "Show wallet transactions for July 2026"
- **Category / Difficulty:** date_time (MEDIUM)
- **Primary Failure:** `WRONG_FINAL_RESPONSE`
- **Failure Reason:** Did not disclose partial result count of 17.
- **Generated SQL:** `SELECT
    wt.id,
    wt.user_id,
    u.name AS user_name,
    wt.amount,
    wt.reference_type,
    wt.remark,
    wt.status,
    wt.transaction_type,
    wt.created_at,
    wt.updated_at
FROM
    wallet_transaction wt
JOIN
    users u ON wt.user_id = u.id
WHERE
    wt.created_at >= '2026-07-01 00:00:00' AND wt.created_at < '2026-08-01 00:00:00'`
- **Final Response:** "Direct Answer:
There are 17 wallet transactions recorded for July 1, 2026.

Explanation:
The database query returned 17 wallet transactions with a `created_at` date of 2026-07-01, which falls within the requested period of July 2026.

Results:
| Id | User Id | User Name | Amount | Reference Type | Remark | Status | Transaction Type | Created At | Updated At |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6,662,347 | 50,225 | Lakshmi Enterprises Retailer | ₹15.00 | cash_point | Successful TFTYAJX##ACM101BTRNK#100 QR scan | 1 | 1 | 2026-07-01 00:34:58 | 2026-07-01 00:34:58 |
| 6,662,348 | 50,225 | Lakshmi Enterprises Retailer | ₹15.00 | cash_point | Successful VNZPXBC##ACM101BTRNK#95 QR scan | 1 | 1 | 2026-07-01 00:34:58 | 2026-07-01 00:34:58 |
| 6,662,349 | 62,977 | Balaji Retail Store | ₹-2,000.00 | withdrawal | Cash Withdrawal | 1 | 0 | 2026-07-01 02:25:13 | 2026-07-01 02:25:13 |
| 6,662,350 | 63,852 | Mahalakshmi Retail Store | ₹-700.00 | withdrawal | Cash Withdrawal | 1 | 0 | 2026-07-01 02:45:13 | 2026-07-01 02:45:13 |
| 6,662,351 | 62,977 | Balaji Retail Store | ₹-2,000.00 | withdrawal | Cash Withdrawal | 1 | 0 | 2026-07-01 06:20:14 | 2026-07-01 06:20:14 |
| 6,662,354 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful kjv1xc5 QR scan | 1 | 1 | 2026-07-01 07:46:17 | 2026-07-01 07:46:17 |
| 6,662,355 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful ycyleay QR scan | 1 | 1 | 2026-07-01 07:49:44 | 2026-07-01 07:49:44 |
| 6,662,356 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful 8lk76b5 QR scan | 1 | 1 | 2026-07-01 07:50:17 | 2026-07-01 07:50:17 |
| 6,662,357 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful 4wjyrxv QR scan | 1 | 1 | 2026-07-01 07:50:52 | 2026-07-01 07:50:52 |
| 6,662,358 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful xv78ja4 QR scan | 1 | 1 | 2026-07-01 07:51:21 | 2026-07-01 07:51:21 |
| 6,662,359 | 56,229 | Royal Retailers | ₹15.00 | cash_point | Successful lqgcvrf QR scan | 1 | 1 | 2026-07-01 07:52:14 | 2026-07-01 07:52:14 |
| 6,662,360 | 56,229 | Royal Retailers | ₹15.00 | cash_point | Successful wqpslgn QR scan | 1 | 1 | 2026-07-01 07:53:30 | 2026-07-01 07:53:30 |
| 6,662,361 | 56,229 | Royal Retailers | ₹15.00 | cash_point | Successful feebiwo QR scan | 1 | 1 | 2026-07-01 07:54:06 | 2026-07-01 07:54:06 |
| 6,662,362 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful kpxfsrz QR scan | 1 | 1 | 2026-07-01 07:54:38 | 2026-07-01 07:54:38 |
| 6,662,363 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful jpurjzy QR scan | 1 | 1 | 2026-07-01 07:55:07 | 2026-07-01 07:55:07 |
| 6,662,365 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful rgjjykl QR scan | 1 | 1 | 2026-07-01 07:55:34 | 2026-07-01 07:55:34 |
| 6,662,367 | 56,229 | Royal Retailers | ₹20.00 | cash_point | Successful adzyfqa QR scan | 1 | 1 | 2026-07-01 07:56:38 | 2026-07-01 07:56:38 |"

### Question #33: "Show top 10 retailers by earnings for July 2026"
- **Category / Difficulty:** top_n (MEDIUM)
- **Primary Failure:** `WRONG_FINAL_RESPONSE`
- **Failure Reason:** Did not disclose partial result count of 2.
- **Generated SQL:** `SELECT 
    u.id AS retailer_id,
    u.name AS retailer_name,
    SUM(wt.amount) AS total_earnings
FROM 
    users u
JOIN 
    wallet_transaction wt ON u.id = wt.user_id
WHERE 
    u.user_role = 2
    AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')
    AND wt.amount > 0
    AND wt.created_at >= '2026-07-01 00:00:00'
    AND wt.created_at < '2026-08-01 00:00:00'
GROUP BY 
    u.id, u.name
ORDER BY 
    total_earnings DESC
LIMIT 10`
- **Final Response:** "Direct Answer:
The top retailers by earnings for July 2026 are Royal Retailers with 225.0 and Lakshmi Enterprises Retailer with 30.0.

Explanation:
Earnings are calculated from the allowed earning transaction types using SUM(wallet_transaction.amount). The database confirms that only two retailers had positive earnings in the specified period, with Royal Retailers ranking first and Lakshmi Enterprises Retailer ranking second.

Results:
| Retailer Id | Retailer | Total Earnings |
| --- | --- | --- |
| 56,229 | Royal Retailers | ₹225.00 |
| 50,225 | Lakshmi Enterprises Retailer | ₹30.00 |"

### Question #61: "Show retailers and their wallet transactions in July 2026"
- **Category / Difficulty:** joins (MEDIUM)
- **Primary Failure:** `WRONG_FINAL_RESPONSE`
- **Failure Reason:** Did not disclose partial result count of 17.
- **Generated SQL:** `SELECT
  u.id AS retailer_id,
  u.name AS retailer_name,
  wt.id AS transaction_id,
  wt.amount,
  wt.transaction_type,
  wt.reference_type,
  wt.remark,
  wt.created_at AS transaction_date
FROM users AS u
JOIN wallet_transaction AS wt
  ON u.id = wt.user_id
WHERE
  u.user_role = 2 AND wt.created_at >= '2026-07-01 00:00:00' AND wt.created_at < '2026-08-01 00:00:00'
ORDER BY
  u.name,
  wt.created_at`
- **Final Response:** "Direct Answer:
In July 2026, Balaji Retail Store

Explanation:
The query returned 17 matching records from the database.

Results:
| Retailer Id | Retailer | Transaction Id | Amount | Transaction Type | Reference Type | Remark | Transaction Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 62,977 | Balaji Retail Store | 6,662,349 | ₹-2,000.00 | 0 | withdrawal | Cash Withdrawal | 2026-07-01 02:25:13 |
| 62,977 | Balaji Retail Store | 6,662,351 | ₹-2,000.00 | 0 | withdrawal | Cash Withdrawal | 2026-07-01 06:20:14 |
| 50,225 | Lakshmi Enterprises Retailer | 6,662,347 | ₹15.00 | 1 | cash_point | Successful TFTYAJX##ACM101BTRNK#100 QR scan | 2026-07-01 00:34:58 |
| 50,225 | Lakshmi Enterprises Retailer | 6,662,348 | ₹15.00 | 1 | cash_point | Successful VNZPXBC##ACM101BTRNK#95 QR scan | 2026-07-01 00:34:58 |
| 63,852 | Mahalakshmi Retail Store | 6,662,350 | ₹-700.00 | 0 | withdrawal | Cash Withdrawal | 2026-07-01 02:45:13 |
| 56,229 | Royal Retailers | 6,662,354 | ₹20.00 | 1 | cash_point | Successful kjv1xc5 QR scan | 2026-07-01 07:46:17 |
| 56,229 | Royal Retailers | 6,662,355 | ₹20.00 | 1 | cash_point | Successful ycyleay QR scan | 2026-07-01 07:49:44 |
| 56,229 | Royal Retailers | 6,662,356 | ₹20.00 | 1 | cash_point | Successful 8lk76b5 QR scan | 2026-07-01 07:50:17 |
| 56,229 | Royal Retailers | 6,662,357 | ₹20.00 | 1 | cash_point | Successful 4wjyrxv QR scan | 2026-07-01 07:50:52 |
| 56,229 | Royal Retailers | 6,662,358 | ₹20.00 | 1 | cash_point | Successful xv78ja4 QR scan | 2026-07-01 07:51:21 |
| 56,229 | Royal Retailers | 6,662,359 | ₹15.00 | 1 | cash_point | Successful lqgcvrf QR scan | 2026-07-01 07:52:14 |
| 56,229 | Royal Retailers | 6,662,360 | ₹15.00 | 1 | cash_point | Successful wqpslgn QR scan | 2026-07-01 07:53:30 |
| 56,229 | Royal Retailers | 6,662,361 | ₹15.00 | 1 | cash_point | Successful feebiwo QR scan | 2026-07-01 07:54:06 |
| 56,229 | Royal Retailers | 6,662,362 | ₹20.00 | 1 | cash_point | Successful kpxfsrz QR scan | 2026-07-01 07:54:38 |
| 56,229 | Royal Retailers | 6,662,363 | ₹20.00 | 1 | cash_point | Successful jpurjzy QR scan | 2026-07-01 07:55:07 |
| 56,229 | Royal Retailers | 6,662,365 | ₹20.00 | 1 | cash_point | Successful rgjjykl QR scan | 2026-07-01 07:55:34 |
| 56,229 | Royal Retailers | 6,662,367 | ₹20.00 | 1 | cash_point | Successful adzyfqa QR scan | 2026-07-01 07:56:38 |"

### Question #69: "Show total July 2026 earnings for retailers linked to distributor 5997"
- **Category / Difficulty:** multi_table (HARD)
- **Primary Failure:** `WRONG_DATABASE_RESULT`
- **Failure Reason:** Result mismatch: Generated 1 rows, Reference 2 rows.
- **Generated SQL:** `SELECT
    SUM(wt.amount) AS total_earnings
FROM
    users u
JOIN
    wallet_transaction wt ON u.id = wt.user_id
JOIN
    retailer_distributor_mappings rdm ON u.id = rdm.retailer_id
WHERE
    u.user_role = 2
    AND rdm.distributor_id = 5997
    AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')
    AND wt.amount > 0
    AND wt.created_at >= '2026-07-01 00:00:00'
    AND wt.created_at < '2026-08-01 00:00:00'`
- **Final Response:** "Direct Answer:
The total July 2026 earnings for retailers linked to distributor 5997 is 255.0.

Explanation:
Earnings are calculated from the allowed earning transaction types using SUM(wallet_transaction.amount).

Results:
| Total Earnings |
| --- |
| ₹255.00 |"

### Question #85: "Compare total wallet balance between retailers and distributors"
- **Category / Difficulty:** comparisons (HARD)
- **Primary Failure:** `WRONG_DATABASE_RESULT`
- **Failure Reason:** Result mismatch: Generated 2 rows, Reference 2 rows.
- **Generated SQL:** `WITH retailer_balances AS (
    SELECT u.id AS retailer_id, u.name AS retailer_name, SUM(wt.amount) AS total_balance
    FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id
    WHERE u.user_role = 2 AND wt.amount > 0
    GROUP BY u.id, u.name
),
distributor_balances AS (
    SELECT u.id AS distributor_id, u.name AS distributor_name, SUM(wt.amount) AS total_balance
    FROM users u JOIN wallet_transaction wt ON u.id = wt.user_id
    WHERE u.user_role = 4 AND wt.amount > 0
    GROUP BY u.id, u.name
)
SELECT 'Retailer' AS type, retailer_id AS user_id, retailer_name AS user_name, total_balance
FROM retailer_balances
UNION ALL
SELECT 'Distributor' AS type, distributor_id AS user_id, distributor_name AS user_name, total_balance
FROM distributor_balances
ORDER BY total_balance DESC`
- **Final Response:** "Direct Answer:
The database results show two retailers with total wallet balances of 225.0 and 30.0, while no distributors are present in the returned data.

Explanation:
The query filtered for users with role 2 (Retailer) and role 4 (Distributor) and summed their positive wallet transaction amounts, but only returned rows for Royal Retailers and Lakshmi Enterprises Retailer, indicating no matching distributor records were found in the result set.

Results:
| Type | User Id | User Name | Total Balance |
| --- | --- | --- | --- |
| Retailer | 56,229 | Royal Retailers | ₹225.00 |
| Retailer | 50,225 | Lakshmi Enterprises Retailer | ₹30.00 |"

### Question #105: "What percentage of total users are retailers?"
- **Category / Difficulty:** percentage_calculations (HARD)
- **Primary Failure:** `WRONG_DATABASE_RESULT`
- **Failure Reason:** Result mismatch: Generated 1 rows, Reference 1 rows.
- **Generated SQL:** `SELECT (COUNT(CASE WHEN user_role = 2 THEN 1 END) / COUNT(*) * 100.0) AS retailer_percentage FROM users`
- **Final Response:** "Direct Answer:
0% of total users are retailers.

Explanation:
The database confirms that the calculated retailer percentage is 0.0.

Results:
| Retailer Percentage |
| --- |
| 0.0 |"

### Question #125: "Show SKU inventories where warehouse is null or missing"
- **Category / Difficulty:** null_handling (MEDIUM)
- **Primary Failure:** `WRONG_FINAL_RESPONSE`
- **Failure Reason:** Did not disclose partial result count of 15.
- **Generated SQL:** `SELECT si.* 
FROM sku_inventories si 
WHERE si.warehouse IS NULL 
   OR si.warehouse = ''`
- **Final Response:** "Direct Answer:
AMC111BTRNK2P#95 is ranked top with 0 for is offline.

Explanation:
The database returned 15 matching records ordered by is offline.

Results:
| Id | Mrp | SKU Code | Unit Price | SKU Description | Invoiced Quantity | Batch Details | Outer Lpn Number | Lpn Number | Carton No | Lpn Code | Packed Quantity | Order Type | Order Reference | Product Id | UOM | Invoice Number | Invoice Date | Warehouse | Invoiced By | Order Date | Customer Info | Distributer Id | Created At | Updated At | Is Callback | Status Wholeseller Id | Status Retailer Id | Sources | Wholesaler Scanned At | Retailer Scanned At | Is Active | Is Offline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3,474,483 | N/A | AMC111BTRNK2P#95 | N/A | MCH PLAIN TRUNK AST. ( 2/10 ) | 0 | N/A | N/A | Wd9N-12 | N/A | N/A | 0 | Distributor | N/A | 281,859 | B10 | 2215404736 | N/A | N/A | N/A | 2025-04-02 | N/A | 6,153 | 2025-02-18 05:30:13 | 2026-07-02 13:46:01 | 1 | N/A | 53,347 | kolkata | N/A | 2026-07-02 13:46:01 | 1 | 0 |
| 3,493,088 | N/A | AMC111BTRNK2P#75 | N/A | MCH PLAIN TRUNK AST. ( 2/10 ) | 0 | N/A | N/A | o-s9-19 | N/A | N/A | 0 | Distributor | N/A | 281,855 | B10 | 8515401297 | N/A | N/A | N/A | 2025-11-02 | N/A | 6,102 | 2025-02-18 12:09:25 | 2026-07-02 11:19:01 | 1 | N/A | 68,083 | kolkata | N/A | 2026-07-02 11:19:01 | 1 | 0 |
| 3,503,068 | N/A | AMC101BMINI#95 | N/A | MCH PLAIN MINI TRUNK AST (1/10) | 0 | N/A | N/A | DCVG-27 | N/A | N/A | 0 | Distributor | N/A | 281,572 | B10 | 8515401389 | N/A | N/A | N/A | 2026-05-02 | N/A | 5,901 | 2025-02-18 12:11:49 | 2026-07-02 12:27:14 | 1 | N/A | 50,231 | kolkata | N/A | 2026-07-02 12:27:14 | 1 | 0 |
| 3,507,563 | N/A | AMC111BTRNK2P#80 | N/A | MCH PLAIN TRUNK AST. ( 2/10 ) | 0 | N/A | N/A | 1zPH-16 | N/A | N/A | 0 | Distributor | N/A | 281,856 | B10 | 2215404948 | N/A | N/A | N/A | 2026-03-02 | N/A | 6,169 | 2025-02-18 12:12:57 | 2026-07-04 19:31:32 | 1 | N/A | 69,599 | kolkata | N/A | 2026-07-04 19:31:32 | 1 | 0 |
| 3,632,609 | N/A | AMC101BMINI2P#100 | N/A | MCH PLAIN MINI TRUNK AST (2/10) | 0 | N/A | N/A | se-n-27 | N/A | N/A | 0 | Distributor | N/A | 281,524 | B10 | 2215405137 | N/A | N/A | N/A | 2025-02-26 | N/A | 6,153 | 2025-02-28 12:17:17 | 2026-07-04 14:07:57 | 1 | N/A | 77,846 | kolkata | N/A | 2026-07-04 14:07:57 | 1 | 0 |
| 3,646,068 | N/A | AGL035BTRNK#100 | N/A | AMUL COMFY FCD TRUNKS POCKET OUTER | 0 | N/A | N/A | dIkQ-47 | N/A | N/A | 0 | Distributor | N/A | 279,438 | B10 | 8515401489 | N/A | N/A | N/A | 2025-02-27 | N/A | 5,871 | 2025-02-28 15:38:56 | 2026-07-05 10:56:44 | 1 | N/A | 71,562 | kolkata | N/A | 2026-07-05 10:56:44 | 1 | 0 |
| 3,646,351 | N/A | AMC101BMINI2P#80 | N/A | MCH PLAIN MINI TRUNK AST (2/10) | 0 | N/A | N/A | ggdn-07 | N/A | N/A | 0 | Distributor | N/A | 281,530 | B10 | 8515401491 | N/A | N/A | N/A | 2025-02-27 | N/A | 5,871 | 2025-02-28 15:39:11 | 2026-07-05 11:13:19 | 1 | N/A | 76,002 | kolkata | N/A | 2026-07-05 11:13:19 | 1 | 0 |
| 14,698,448 | N/A | AMC061BBRIF2AST#95 | N/A | MCH SMART CUT BRIEF AST (2/10) | 0 | N/A | N/A | B8qM-19 | N/A | N/A | 0 | Distributor | N/A | 281,402 | B10 | 2015406445 | 2025-03-18 | N/A | N/A | 2025-03-18 | N/A | 6,090 | 2025-03-18 15:30:25 | 2026-07-03 13:32:36 | 1 | N/A | 67,933 | kolkata | N/A | 2026-07-03 13:32:36 | 1 | 0 |
| 14,698,484 | N/A | AMC061BBRIF2AST#95 | N/A | MCH SMART CUT BRIEF AST (2/10) | 0 | N/A | N/A | KI4G-27 | N/A | N/A | 0 | Distributor | N/A | 281,402 | B10 | 2015406445 | 2025-03-18 | N/A | N/A | 2025-03-18 | N/A | 6,090 | 2025-03-18 15:30:26 | 2026-07-03 13:43:28 | 1 | N/A | 52,809 | kolkata | N/A | 2026-07-03 13:43:28 | 1 | 0 |
| 14,832,088 | N/A | ACM061BRN#XXL | N/A | AMUL COMFY GYM VEST AST | 0 | N/A | N/A | OXAPSG | N/A | N/A | 0 | Distributor | N/A | 271,700 | B5 | 2215405177 | N/A | N/A | N/A | 2025-03-01 | N/A | 6,167 | 2025-03-21 15:48:53 | 2026-07-01 11:56:15 | 1 | N/A | 74,601 | tirupur | N/A | 2026-07-01 11:56:15 | 1 | 0 |
| 14,918,493 | N/A | ACM023BTRNK2AST#95 | N/A | AMUL COMFY COLOUR B TRUNKS OE 2/10 | 0 | N/A | N/A | PAPXZFR | N/A | N/A | 0 | Distributor | N/A | 270,967 | B10 | 6151059319 | N/A | N/A | N/A | 2025-03-22 | N/A | 6,167 | 2025-03-24 15:40:23 | 2026-07-01 15:27:40 | 1 | N/A | 62,617 | tirupur | N/A | 2026-07-01 15:27:40 | 1 | 0 |
| 14,953,301 | N/A | ACM061BRN#XL | N/A | AMUL COMFY GYM VEST AST | 0 | N/A | N/A | WCJSSHS | N/A | N/A | 0 | Distributor | N/A | 271,698 | B5 | 2215405602 | N/A | N/A | N/A | 2025-03-24 | N/A | 6,171 | 2025-03-25 15:02:20 | 2026-07-02 13:31:23 | 1 | N/A | 51,345 | tirupur | N/A | 2026-07-02 13:31:23 | 1 | 0 |
| 14,990,586 | N/A | AMC061BBRIF2AST#85 | N/A | MCH SMART CUT BRIEF AST (2/10) | 0 | N/A | N/A | sbXC-03 | N/A | N/A | 0 | Distributor | N/A | 281,400 | B10 | 2215405678 | 2025-03-26 | N/A | N/A | 2025-03-26 | N/A | 6,121 | 2025-03-26 23:02:59 | 2026-07-01 19:57:43 | 1 | N/A | 48,857 | kolkata | N/A | 2026-07-01 19:57:43 | 1 | 0 |
| 14,990,994 | N/A | AMC101BMINI#85 | N/A | MCH PLAIN MINI TRUNK AST (1/10) | 0 | N/A | N/A | WLu0-13 | N/A | N/A | 0 | Distributor | N/A | 281,570 | B10 | 8515401798 | 2025-03-26 | N/A | N/A | 2025-03-26 | N/A | 5,906 | 2025-03-26 23:03:14 | 2026-07-02 19:58:03 | 1 | N/A | 76,454 | kolkata | N/A | 2026-07-02 19:58:03 | 1 | 0 |
| 14,991,269 | N/A | AMC058SBRIF#55 | N/A | MACHO BOY SMART CUT O.E COL BRF | 0 | N/A | N/A | XBkY-22 | N/A | N/A | 0 | Distributor | N/A | 281,283 | B10 | 8515401793 | 2025-03-26 | N/A | N/A | 2025-03-26 | N/A | 5,903 | 2025-03-26 23:03:22 | 2026-07-02 12:20:17 | 1 | N/A | 72,919 | kolkata | N/A | 2026-07-02 12:20:17 | 1 | 0 |"

### Question #131: "Show all withdrawal transactions with negative amounts in July 2026"
- **Category / Difficulty:** negative_values (MEDIUM)
- **Primary Failure:** `WRONG_FINAL_RESPONSE`
- **Failure Reason:** Did not disclose partial result count of 17.
- **Generated SQL:** `SELECT
    wt.id AS transaction_id,
    wt.user_id,
    u.name AS user_name,
    wt.amount,
    wt.reference_type,
    wt.remark,
    wt.created_at
FROM
    wallet_transaction wt
LEFT JOIN
    users u ON wt.user_id = u.id
WHERE
    wt.reference_type = 'withdrawal'
    AND wt.amount < 0
    AND wt.created_at >= '2026-07-01 00:00:00'
    AND wt.created_at < '2026-08-01 00:00:00'
ORDER BY
    wt.created_at DESC`
- **Final Response:** "Direct Answer:
There are 17 withdrawal transactions with negative amounts recorded in July 2026, all dated July 1, 2026, with amounts ranging from -500.0 to -5000.0.

Explanation:
The database confirms 17 rows where reference_type is 'withdrawal', amount is less than 0, and created_at falls within July 2026, with user names listed as N/A for 15 entries and specific store names for the remaining two.

Results:
| Transaction Id | User Id | User Name | Amount | Reference Type | Remark | Created At |
| --- | --- | --- | --- | --- | --- | --- |
| 6,662,772 | 49,263 | N/A | ₹-3,100.00 | withdrawal | Cash Withdrawal | 2026-07-01 10:35:36 |
| 6,662,770 | 74,474 | N/A | ₹-2,160.00 | withdrawal | Cash Withdrawal | 2026-07-01 10:35:19 |
| 6,662,740 | 52,061 | N/A | ₹-3,045.00 | withdrawal | Cash Withdrawal | 2026-07-01 10:25:14 |
| 6,662,683 | 50,341 | N/A | ₹-5,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 10:10:17 |
| 6,662,679 | 77,738 | N/A | ₹-810.00 | withdrawal | Cash Withdrawal | 2026-07-01 10:05:18 |
| 6,662,619 | 51,270 | N/A | ₹-3,500.00 | withdrawal | Cash Withdrawal | 2026-07-01 09:50:14 |
| 6,662,568 | 68,054 | N/A | ₹-1,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 09:40:14 |
| 6,662,551 | 62,429 | N/A | ₹-2,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 09:35:20 |
| 6,662,545 | 66,100 | N/A | ₹-500.00 | withdrawal | Cash Withdrawal | 2026-07-01 09:30:14 |
| 6,662,436 | 56,312 | N/A | ₹-700.00 | withdrawal | Cash Withdrawal | 2026-07-01 09:05:17 |
| 6,662,430 | 49,477 | N/A | ₹-4,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 08:50:14 |
| 6,662,364 | 54,276 | N/A | ₹-1,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 07:55:14 |
| 6,662,353 | 59,767 | N/A | ₹-580.00 | withdrawal | Cash Withdrawal | 2026-07-01 07:35:15 |
| 6,662,352 | 62,357 | N/A | ₹-755.00 | withdrawal | Cash Withdrawal | 2026-07-01 07:15:13 |
| 6,662,351 | 62,977 | Balaji Retail Store | ₹-2,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 06:20:14 |
| 6,662,350 | 63,852 | Mahalakshmi Retail Store | ₹-700.00 | withdrawal | Cash Withdrawal | 2026-07-01 02:45:13 |
| 6,662,349 | 62,977 | Balaji Retail Store | ₹-2,000.00 | withdrawal | Cash Withdrawal | 2026-07-01 02:25:13 |"

### Question #145: "Show top 10 retailers by earnings for July 2026"
- **Category / Difficulty:** fewer_than_requested (MEDIUM)
- **Primary Failure:** `WRONG_FINAL_RESPONSE`
- **Failure Reason:** Did not disclose partial result count of 2.
- **Generated SQL:** `SELECT u.id AS retailer_id, u.name AS retailer_name, SUM(wt.amount) AS total_earnings
FROM users u
JOIN wallet_transaction wt ON u.id = wt.user_id
WHERE u.user_role = 2
  AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')
  AND wt.amount > 0
  AND wt.created_at >= '2026-07-01 00:00:00'
  AND wt.created_at < '2026-08-01 00:00:00'
GROUP BY u.id, u.name
ORDER BY total_earnings DESC
LIMIT 10`
- **Final Response:** "Direct Answer:
The highest‑earning retailers in July 2026 are Royal Retailers with total earnings of 225.0, followed by Lakshmi Enterprises Retailer with total earnings of 30.0.

Explanation:
Earnings are calculated from the allowed earning transaction types using SUM(wallet_transaction.amount).

Results:
| Retailer Id | Retailer | Total Earnings |
| --- | --- | --- |
| 56,229 | Royal Retailers | ₹225.00 |
| 50,225 | Lakshmi Enterprises Retailer | ₹30.00 |"

### Question #153: "Show me the data"
- **Category / Difficulty:** ambiguous_natural_language (HARD)
- **Primary Failure:** `WRONG_INTENT`
- **Failure Reason:** Ambiguous query failed to trigger clarification.
- **Generated SQL:** `SELECT u.id AS retailer_id, u.name AS retailer_name, SUM(qpm.box_calulation_um) AS total_boxes_scanned, SUM(wt.amount) AS total_earnings
FROM users u
LEFT JOIN qr_point_map qpm ON u.id = qpm.retailer_id
LEFT JOIN wallet_transaction wt ON u.id = wt.user_id
WHERE u.user_role = 2
  AND qpm.retailer_scanned_at >= '2026-07-01 00:00:00'
  AND qpm.retailer_scanned_at < '2026-08-01 00:00:00'
  AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')
  AND wt.amount > 0
  AND wt.created_at >= '2026-07-01 00:00:00'
  AND wt.created_at < '2026-08-01 00:00:00'
GROUP BY u.id, u.name
ORDER BY total_boxes_scanned DESC, total_earnings DESC
LIMIT 5`
- **Final Response:** "SQL Validation Failed: Column 'retailer_id' does not exist in table 'qr_point_map'. Valid columns include: box_calculation_uom, box_calulation_um, box_count_value, created_at, distributor_cash_points, gride_type, id, ka_box_value, m_g_box_value, pcs_calculation_uom"
