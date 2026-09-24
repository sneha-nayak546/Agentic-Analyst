import json
import time
from app.database.read_executor import execute_read_query

def main():
    t0 = time.time()
    print("Testing Live Dashboard Queries...")

    # 1. Total counts
    q_roles = "SELECT user_role, COUNT(id) AS cnt FROM users WHERE user_role IN (2, 4) GROUP BY user_role;"
    r_roles = execute_read_query(q_roles)
    print("Roles:", r_roles.get("data"))

    # 2. Top distributors
    q_dist = """
    SELECT u.id, u.name, COALESCE(s.sname, 'Other') AS region,
           ROUND(COALESCE(SUM(wt.amount), 0), 2) AS raw_earnings,
           u.status
    FROM users u
    JOIN wallet_transaction wt ON u.id = wt.user_id
    LEFT JOIN state s ON u.state_id = s.id
    WHERE u.user_role = 4
      AND wt.amount > 0
      AND wt.reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')
    GROUP BY u.id, u.name, s.sname, u.status
    ORDER BY raw_earnings DESC
    LIMIT 5;
    """
    r_dist = execute_read_query(q_dist)
    print("Top Distributors:", r_dist.get("data"))

    # 3. Monthly trend (last 5 months)
    q_trend = """
    SELECT DATE_FORMAT(created_at, '%b %Y') AS month,
           DATE_FORMAT(created_at, '%Y-%m') AS sort_key,
           ROUND(COALESCE(SUM(amount), 0) / 10000000.0, 3) AS revenue,
           COUNT(id) AS transactions
    FROM wallet_transaction
    WHERE amount > 0 AND reference_type IN ('topup', 'cash_point', 'referral_earning', 'coupon_redeem')
    GROUP BY sort_key, month
    ORDER BY sort_key DESC
    LIMIT 5;
    """
    r_trend = execute_read_query(q_trend)
    print("Monthly Trend:", r_trend.get("data"))

    print(f"Completed in {round(time.time() - t0, 2)}s")

if __name__ == "__main__":
    main()
