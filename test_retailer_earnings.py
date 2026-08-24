from app.agent.sql_agent import run_agent

def main():
    question = "who all are retailers available in the users table, for those retailers how much they all are earning in this month: cash_point, referral earning, topup, coupon_redeem"
    print(f"Running Agent with Question:\n'{question}'\n")
    res = run_agent(question)
    
    print("=" * 70)
    print("STATUS:", res.get("status"))
    print("GENERATED SQL:\n", res.get("generated_sql"))
    print("\nOPTIMIZED SQL:\n", res.get("optimized_sql"))
    print("\nEXECUTION SUCCESS:", res.get("execution", {}).get("success"))
    print("ROW COUNT:", res.get("execution", {}).get("row_count"))
    if res.get("execution", {}).get("data"):
        print("SAMPLE ROW:", res["execution"]["data"][0])
    print("=" * 70)

    if res.get("status") == "success" and res.get("execution", {}).get("success"):
        print("\nSUCCESS: Retailer earnings query generated and executed with 0 column errors!")
    else:
        print("\nFAILURE:", res.get("execution", {}).get("error") or res.get("validation", {}).get("reason"))

if __name__ == "__main__":
    main()
