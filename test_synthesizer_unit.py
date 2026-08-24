from app.llm.sql_generator import _synthesize_sql_from_prompt

tests = [
    (
        'Earnings breakdown (this month)',
        "Table `users` with columns: [id, name, mobile_number, user_role, created_at]\n"
        "Table `wallet_transaction` with columns: [id, user_id, amount, reference_type, created_at]\n"
        "Required Joins: users.id = wallet_transaction.user_id\n"
        "- Time Filter: created_at >= DATE_FORMAT(NOW(), '%Y-%m-01')\n"
        "Business Question: all retailers earnings this month referral topup cashback coupon"
    ),
    (
        'Last 7 days earnings',
        "Table `users` with columns: [id, name, mobile_number, user_role, created_at]\n"
        "Table `wallet_transaction` with columns: [id, user_id, amount, reference_type, created_at]\n"
        "Required Joins: users.id = wallet_transaction.user_id\n"
        "- Time Filter: created_at >= NOW() - INTERVAL 7 DAY\n"
        "Business Question: retailer earnings last 7 days referral topup cashback"
    ),
    (
        'User listing (shop owners)',
        "Table `users` with columns: [id, name, email, mobile_number, user_role, wallet_balance, status, created_at]\n"
        "Required Joins: None\n"
        "Business Question: show me all shop owners with their mobile number"
    ),
    (
        'Withdrawal query',
        "Table `users` with columns: [id, name, mobile_number, user_role]\n"
        "Table `wallet_transaction` with columns: [id, user_id, amount, reference_type, remark, created_at]\n"
        "Required Joins: users.id = wallet_transaction.user_id\n"
        "Business Question: show all retailer withdrawals this month"
    ),
    (
        'Count retailers',
        "Table `users` with columns: [id, name, user_role, created_at]\n"
        "Required Joins: None\n"
        "Business Question: how many retailers are there"
    ),
    (
        'Wallet balance of dealers',
        "Table `users` with columns: [id, name, mobile_number, user_role, wallet_balance]\n"
        "Required Joins: None\n"
        "Business Question: show wallet balance of all dealers"
    ),
    (
        'Credit transactions',
        "Table `users` with columns: [id, name, mobile_number]\n"
        "Table `wallet_transaction` with columns: [id, user_id, amount, transaction_type, reference_type, remark, created_at]\n"
        "Required Joins: users.id = wallet_transaction.user_id\n"
        "Business Question: show all credit transactions for retailers"
    ),
    (
        'Wholesaler count',
        "Table `users` with columns: [id, name, user_role]\n"
        "Required Joins: None\n"
        "Business Question: how many wholesalers are registered"
    ),
]

all_pass = True
for name, prompt in tests:
    sql = _synthesize_sql_from_prompt(prompt)
    ok = 'SELECT' in sql and ';' in sql and not sql.strip().endswith(',;')
    status = 'PASS' if ok else 'FAIL'
    if not ok:
        all_pass = False
    print(f'[{status}] {name}')
    print(f'       {sql[:180]}')
    print()

print('ALL TESTS PASSED!' if all_pass else 'SOME TESTS FAILED!')
