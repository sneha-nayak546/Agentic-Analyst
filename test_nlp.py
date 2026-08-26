import json
import time
import concurrent.futures
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.nlp_understanding import nlp_agent

def run_query(query, timeout=30):
    start = time.time()
    def _run():
        return nlp_agent.parse_question(query)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        try:
            result = future.result(timeout=timeout)
            elapsed = time.time() - start
            return True, elapsed, result
        except concurrent.futures.TimeoutError:
            return False, timeout, "Timeout"
        except Exception as e:
            return False, time.time() - start, f"Error: {e}"

def main():
    queries = {
        "Simple": "Show all retailers",
        "Complex": "Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings for the current month."
    }
    
    for name, q in queries.items():
        print(f"--- Running {name} Test ---")
        print(f"Query: {q}")
        success, duration, result = run_query(q, 30)
        
        if not success:
            print(f"Result: FAIL ({result}) after {duration:.2f}s")
        else:
            print(f"Result: SUCCESS in {duration:.2f}s")
            try:
                res_dict = getattr(result, 'model_dump', lambda: result.__dict__)()
                print(json.dumps(res_dict, default=str, indent=2))
            except Exception as e:
                print(f"Failed to convert to dict: {e}")
                print(result)
        print("\n")

if __name__ == "__main__":
    main()
