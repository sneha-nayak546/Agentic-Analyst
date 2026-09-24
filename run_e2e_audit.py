import json
import traceback
from app.agent.sql_agent import run_agent

TEST_CASES = [
    # 1-3 conversational chain
    "Show Karnataka distributors",
    "What are their earnings?",
    "Which one has the highest earnings?",
    
    # 4-6 conversational chain
    "Show retailers linked to distributor 5997 with their individual earnings for the current month.",
    "Compare their earnings with last month.",
    "What is the percentage change?",
    
    # Random queries
    "Show TDS deducted.",
    "Show withdrawal requests for August.",
    
    # ID tests
    "Show ID 5997.",
    "Show ID 999999999.",
    
    # Standalone query to break context
    "What is the total number of approved retailers?",
    
    # Duplicate query to check caching/idempotency
    "What is the total number of approved retailers?",
]

def run_audit():
    print("==================================================")
    print("AGENTIC E2E ACCURACY AUDIT")
    print("==================================================\n")
    
    context = {}
    
    for i, question in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] USER QUESTION: {question}")
        print("-" * 50)
        try:
            res = run_agent(question, context=context)
            
            # Update context for follow-ups
            if not res.get("is_ambiguous") and res.get("context"):
                context = res["context"]
                
            debug = res.get("debug_pipeline", {})
            
            print(f"→ Requirement JSON       : {json.dumps(debug.get('intent', 'N/A'))}")
            print(f"→ Resolved entities/IDs  : {debug.get('entity', 'N/A')}")
            print(f"→ Relationship/join plan : {', '.join(debug.get('tables', []))}")
            print(f"→ Generated SQL          : {debug.get('sql', 'N/A')}")
            
            exec_res = debug.get('execution', {})
            print(f"→ SQL execution result   : Success={exec_res.get('success')}, Rows={exec_res.get('row_count')}")
            
            val_res = debug.get('validation', {})
            print(f"→ Result validation      : {res.get('validation_status')} - {val_res.get('status')} {val_res.get('reason', '')}")
            
            diff_text = res.get('requirement_diff')
            if diff_text:
                print(f"→ Requirement Diff       :\n{diff_text}")
                
            print(f"→ Final response         : {res.get('summary', res.get('clarification', 'No response'))}")
            
        except Exception as e:
            print(f"CRASH: {traceback.format_exc()}")

if __name__ == "__main__":
    run_audit()
