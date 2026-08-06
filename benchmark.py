import time
import pandas as pd
from app.agent.sql_agent import run_agent

BENCHMARK_QUERIES = [
    "Show wallet transactions for July 2026",
    "Show wallet transactions for August 2026",  # Template cache test
    "Show top 10 users by wallet balance",       # Predefined query test
    "Show withdrawal requests summary",
    "Show sku inventories stock price",
    "Show company list",
    "Show machine details",
    "Show automatic transactions bank report",
    "Show wallet transactions for July 2026"     # Exact cache test
]

def run_benchmark():
    print("=" * 80)
    print("        AI SQL AGENT BACKEND SPEED BENCHMARK RUNNER")
    print("=" * 80)
    
    results = []

    for idx, query in enumerate(BENCHMARK_QUERIES, 1):
        print(f"\n[{idx}/{len(BENCHMARK_QUERIES)}] Query: '{query}'")
        t0 = time.time()
        res = run_agent(query, execute=True)
        t_total = round((time.time() - t0) * 1000, 2)

        bm = res.get("benchmarks", {})
        results.append({
            "Query": query[:35] + ("..." if len(query) > 35 else ""),
            "Status": res.get("status", "unknown"),
            "Intent (ms)": bm.get("intent_detection_ms", 0.0),
            "Schema (ms)": bm.get("schema_lookup_ms", 0.0),
            "Prompt (ms)": bm.get("prompt_build_ms", 0.0),
            "LLM (ms)": bm.get("llm_generation_ms", 0.0),
            "Valid (ms)": bm.get("validation_ms", 0.0),
            "Exec (ms)": bm.get("execution_ms", 0.0),
            "Total (ms)": bm.get("total_ms", t_total),
            "Rows": res.get("execution", {}).get("row_count", 0)
        })

    df = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print("                      BENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    print(df.to_string(index=False))
    print("=" * 80)

    avg_uncached_llm = df[df["LLM (ms)"] > 0]["LLM (ms)"].mean() if not df[df["LLM (ms)"] > 0].empty else 0.0
    print(f"\nAverage Uncached LLM Generation Time : {avg_uncached_llm:.2f} ms")
    print(f"Fastest Query Total Time             : {df['Total (ms)'].min():.2f} ms")
    print(f"Average Pipeline Response Time       : {df['Total (ms)'].mean():.2f} ms")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()

