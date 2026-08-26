import os
import time
import requests
import json
import psutil
from dotenv import load_dotenv
import pandas as pd
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.nlp_understanding import nlp_agent
from app.knowledge.relationship_resolver import relationship_resolver
from app.prompt.prompt_builder import build_sql_prompt

load_dotenv()

QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen2.5-coder:7b")

QUESTIONS = [
    "What is the total wallet amount across all users?",
    "Show me the top 5 retailers by revenue in July 2026.",
    "Which distributors have inactive linked retailers?",
    "Count the number of users who have more than 5 wallet transactions.",
    "Show the distributor ID and total balance for the distributor with the highest balance."
]

def get_system_usage():
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    return cpu, ram

def run_query_e2e(question: str):
    print(f"\n" + "="*50)
    print(f"QUERY: {question}")
    
    t0 = time.time()
    
    cpu_start, ram_start = get_system_usage()
    
    # 1. NLP Intent
    t_nlp = time.time()
    req = nlp_agent.parse_question(question)
    nlp_time = time.time() - t_nlp
    print(f"[NLP] Intent: {req.intent} | Entities: {req.entities} ({nlp_time*1000:.2f}ms)")
    
    # 2. Hybrid RAG & Query Plan
    t_plan = time.time()
    plan = relationship_resolver.resolve(req)
    plan_time = time.time() - t_plan
    print(f"[RAG/PLAN] Tables: {plan.relevant_tables} ({plan_time*1000:.2f}ms)")
    
    # 3. Prompt Builder
    prompt = build_sql_prompt(plan)
    
    # 4. LLM SQL Generation
    t_llm = time.time()
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": QWEN_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 300,
        "stream": True,
        "stream_options": {"include_usage": True}
    }
    
    first_token_time = None
    full_response = ""
    total_tokens = 0
    sql_gen_time = 0
    ttft = 0
    error = None
    
    try:
        base = QWEN_BASE_URL.rstrip('/')
        if not base.endswith("chat/completions"):
            endpoint = f"{base}/chat/completions"
        else:
            endpoint = base
            
        response = requests.post(endpoint, headers=headers, json=payload, stream=True, timeout=300)
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith("data: "):
                    data_str = line_text[6:]
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data_str)
                        if first_token_time is None and len(chunk.get('choices', [])) > 0:
                            first_token_time = time.time() - t_llm
                            ttft = first_token_time * 1000
                        
                        if 'usage' in chunk and chunk['usage']:
                            total_tokens = chunk['usage'].get('completion_tokens', 0)
                            
                        if len(chunk.get('choices', [])) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                full_response += delta['content']
                    except json.JSONDecodeError:
                        pass
                        
        sql_gen_time = time.time() - t_llm
        if total_tokens == 0:
            total_tokens = len(full_response) / 4.0 # approximate if no usage returned
            
        tps = total_tokens / sql_gen_time if sql_gen_time > 0 else 0
        print(f"[SQL GENERATION] TTFT: {ttft:.2f}ms | Total Gen Time: {sql_gen_time*1000:.2f}ms | TPS: {tps:.2f}")
        
    except Exception as e:
        error = str(e)
        print(f"[ERROR] LLM Request Failed: {e}")
        
    total_time = time.time() - t0
    cpu_end, ram_end = get_system_usage()
    
    result = {
        "question": question,
        "nlp_time_ms": nlp_time * 1000,
        "plan_time_ms": plan_time * 1000,
        "sql_gen_time_ms": sql_gen_time * 1000,
        "ttft_ms": ttft,
        "total_time_ms": total_time * 1000,
        "tokens_per_sec": tps if not error else 0,
        "total_tokens": total_tokens,
        "cpu_start": cpu_start,
        "ram_start": ram_start,
        "cpu_end": cpu_end,
        "ram_end": ram_end,
        "error": error,
        "response_len": len(full_response)
    }
    return result

def run_benchmark():
    if not QWEN_BASE_URL:
        print("❌ QWEN_BASE_URL is not set.")
        return
        
    print(f"Starting Benchmark against Endpoint: {QWEN_BASE_URL}")
    results = []
    
    print("Running warmup query to load model...")
    try:
        requests.post(f"{QWEN_BASE_URL.rstrip('/')}/chat/completions", 
                     json={"model": QWEN_MODEL, "messages": [{"role": "user", "content": "hello"}], "max_tokens": 10},
                     headers={"Authorization": f"Bearer {QWEN_API_KEY}"})
    except Exception as e:
        print(f"Warmup failed: {e}")
                 
    for q in QUESTIONS:
        res = run_query_e2e(q)
        results.append(res)
        time.sleep(1) # brief pause
        
    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    print("\n" + "="*50)
    print("BENCHMARK COMPLETE")
    print(df[['question', 'total_time_ms', 'sql_gen_time_ms', 'tokens_per_sec']].to_string())
    print("Saved to benchmark_results.csv")
    
    avg_latency = df['total_time_ms'].mean()
    print(f"Avg Latency: {avg_latency:.2f}ms")

if __name__ == "__main__":
    run_benchmark()
