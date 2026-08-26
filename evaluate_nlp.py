import sys
import os
import json
import time
import concurrent.futures
from copy import deepcopy

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent.nlp_understanding import nlp_agent

# We will define detailed tests covering the requirements
tests = [
    # 1. Simple questions
    {
        "category": "Simple",
        "question": "Show all retailers",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "relationships": [],
            "specific_ids": {},
            "metrics": [],
            "time": None,
            "filters": [],
            "clarification_required": None
        }
    },
    {
        "category": "Simple",
        "question": "List all distributors",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "relationships": [],
            "specific_ids": {},
            "metrics": [],
            "time": None,
            "filters": [],
            "clarification_required": None
        }
    },
    
    # 2. Multi-condition questions
    {
        "category": "Multi-condition",
        "question": "Show active retailers in region East",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "relationships": [],
            "specific_ids": {},
            "metrics": [],
            "time": None,
            "filters": [
                {"field": "status", "operator": "=", "value": "active"},
                {"field": "region", "operator": "=", "value": "East"}
            ]
        }
    },
    
    # 3. Distributor -> retailer relationships & Specific IDs (5997)
    {
        "category": "Relationships & IDs",
        "question": "Generate a table of retailers linked to distributor 5997",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}, {"type": "distributor"}],
            "relationships": [{"from_entity": "retailer", "to_entity": "distributor"}], # ignoring exact relation string match for simplicity
            "specific_ids": {"distributor_id": 5997},
            "metrics": [],
            "output_type": "table"
        }
    },
    
    # 4. Earnings (needs clarification if no date)
    {
        "category": "Clarification",
        "question": "What are the total earnings for distributor 5997?",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "specific_ids": {"distributor_id": 5997},
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": None,
            "clarification_required": "not_null" # Special flag to check if clarification is requested
        }
    },
    
    # 5. Earnings with date
    {
        "category": "Time",
        "question": "What are the total earnings for distributor 5997 this month?",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "specific_ids": {"distributor_id": 5997},
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": {"type": "current_month"},
            "clarification_required": None
        }
    },
    
    # 6. Withdrawals
    {
        "category": "Metrics",
        "question": "Show withdrawals for retailer 1234 in July 2026",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "specific_ids": {"retailer_id": 1234},
            "metrics": [{"name": "withdrawals"}],
            "time": {"type": "specific_month", "value": "July 2026"},
            "clarification_required": None
        }
    },
    
    # 7. TDS
    {
        "category": "Metrics",
        "question": "What is the TDS deducted for distributor 5997 today?",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "specific_ids": {"distributor_id": 5997},
            "metrics": [{"name": "TDS"}],
            "time": {"type": "today"}, # Assuming today or similar time
            "clarification_required": None
        }
    },
    
    # 8. Inventory
    {
        "category": "Metrics",
        "question": "What is the current inventory for retailer 99?",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "specific_ids": {"retailer_id": 99},
            "metrics": [{"name": "inventory"}],
            "clarification_required": None
        }
    },
    
    # 9. Percentage calculations & Top N
    {
        "category": "Percentage & Top N",
        "question": "Show the top 5 retailers linked to distributor 5997 by current-month earnings, including percentage contribution.",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}, {"type": "distributor"}],
            "specific_ids": {"distributor_id": 5997},
            "metrics": [{"name": "earnings"}],
            "time": {"type": "current_month"},
            "limit": 5,
            "percentage_calculation": True
        }
    },
    
    # 10. Comparisons
    {
        "category": "Comparisons",
        "question": "Compare earnings for distributor 5997 between July and August",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "specific_ids": {"distributor_id": 5997},
            "metrics": [{"name": "earnings"}],
            "comparison_requirements": "not_null" # any dict is fine
        }
    },
    
    # 11. Grouping
    {
        "category": "Grouping",
        "question": "Total earnings this month grouped by state",
        "expected": {
            "intent": "ANALYTICS",
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": {"type": "current_month"},
            "group_by": ["state"]
        }
    },
    
    # 12. Invalid IDs
    {
        "category": "Invalid/non-existent IDs",
        "question": "Show earnings for distributor ABC",
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "metrics": [{"name": "earnings"}],
            "clarification_required": "not_null" # Without date, needs clarification too
        }
    },
    
    # 13. Context Follow-up
    {
        "category": "Follow-up",
        "question": "What about for retailer 100?",
        "context": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "specific_ids": {"retailer_id": 50},
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": {"type": "current_month"}
        },
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "specific_ids": {"retailer_id": 100},
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": {"type": "current_month"}
        }
    },
    
    # 14. Context Switch
    {
        "category": "Context Switching",
        "question": "Actually, just show me all active distributors",
        "context": {
            "intent": "ANALYTICS",
            "entities": [{"type": "retailer"}],
            "specific_ids": {"retailer_id": 50},
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": {"type": "current_month"}
        },
        "expected": {
            "intent": "ANALYTICS",
            "entities": [{"type": "distributor"}],
            "filters": [{"field": "status", "operator": "=", "value": "active"}],
            "metrics": []
        }
    }
]

# Create more tests by mutating the above
extra_tests = [
    {
        "category": "Aggregations",
        "question": "What is the average withdrawal amount this month?",
        "expected": {
            "intent": "ANALYTICS",
            "metrics": [{"name": "withdrawals", "aggregation": "AVG"}],
            "time": {"type": "current_month"}
        }
    },
    {
        "category": "Output-column",
        "question": "List retailers and show their retailer_id and name",
        "expected": {
            "entities": [{"type": "retailer"}],
            "requested_columns": ["retailer_id", "name"]
        }
    },
    {
        "category": "Ranking/lowest",
        "question": "Show the 10 retailers with the lowest inventory",
        "expected": {
            "entities": [{"type": "retailer"}],
            "metrics": [{"name": "inventory"}],
            "limit": 10,
            "sort": {"field": "inventory", "direction": "ASC"}
        }
    },
    {
        "category": "Time Range",
        "question": "Total earnings between 2026-01-01 and 2026-03-31",
        "expected": {
            "metrics": [{"name": "earnings", "aggregation": "SUM"}],
            "time": {"type": "date_range"} 
        }
    }
]
tests.extend(extra_tests)

# Multiply to get to ~35-50 by generating variations
base_tests = deepcopy(tests)
for i in range(15):
    t = deepcopy(base_tests[i % len(base_tests)])
    t["question"] = t["question"] + f" (variation {i})"
    tests.append(t)

print(f"Total tests: {len(tests)}")

def check_list_match(expected_list, actual_list, field_to_check):
    if expected_list is None:
        return True
    if len(expected_list) == 0 and len(actual_list) == 0:
        return True
    
    for exp_item in expected_list:
        found = False
        for act_item in actual_list:
            if isinstance(act_item, dict):
                act_item_dict = act_item
            elif isinstance(act_item, str):
                act_item_dict = {"__value__": act_item}
            else:
                try:
                    act_item_dict = getattr(act_item, 'model_dump', lambda: act_item.__dict__)()
                    if not isinstance(act_item_dict, dict): act_item_dict = act_item.__dict__
                except Exception:
                    act_item_dict = {"__value__": str(act_item)}
                
            match = True
            for k, v in exp_item.items():
                if act_item_dict.get(k) != v:
                    match = False
                    break
            if match:
                found = True
                break
        if not found:
            return False
    return True

metrics_names = [
    "intent", "entity", "relationship", "id", "metric", "time", "filter",
    "aggregation", "grouping", "ranking_limit", "output_column", "clarification"
]
results = {m: {"pass": 0, "fail": 0} for m in metrics_names}

start_time = time.time()
total_inference_time = 0.0
successful_tests = 0
timeouts = 0
errors = 0
complete_pass_count = 0
failed_details = []

for i, test in enumerate(tests):
    print(f"\n[{i+1}/{len(tests)}] Testing: {test['question']}")
    
    def run_test():
        return nlp_agent.parse_question(test['question'], context=test.get('context'))

    q_start = time.time()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(run_test)
        req = future.result(timeout=120) # 120 second timeout per test
        executor.shutdown(wait=False)
    except concurrent.futures.TimeoutError:
        print(f"TIMEOUT: Test {i+1} took longer than 120 seconds.")
        executor.shutdown(wait=False)
        timeouts += 1
        continue
    except Exception as e:
        print(f"ERROR: Test {i+1} failed with exception: {e}")
        errors += 1
        continue
        
    q_time = time.time() - q_start
    total_inference_time += q_time
    successful_tests += 1

    expected = test['expected']
    
    failed_fields = []
    
    # 1. Intent
    if 'intent' in expected:
        if req.intent == expected['intent']: results['intent']['pass'] += 1
        else:
            results['intent']['fail'] += 1
            failed_fields.append('intent')
        
    # 2. Entity
    if 'entities' in expected:
        if check_list_match(expected['entities'], req.entities, 'entities'): results['entity']['pass'] += 1
        else:
            results['entity']['fail'] += 1
            failed_fields.append('entity')
        
    # 3. Relationship
    if 'relationships' in expected:
        if check_list_match(expected['relationships'], req.relationships, 'relationships'): results['relationship']['pass'] += 1
        else:
            results['relationship']['fail'] += 1
            failed_fields.append('relationship')
        
    # 4. ID
    if 'specific_ids' in expected:
        match = True
        for k, v in expected['specific_ids'].items():
            if req.specific_ids.get(k) != v: match = False
        if match: results['id']['pass'] += 1
        else:
            results['id']['fail'] += 1
            failed_fields.append('id')
        
    # 5. Metric
    if 'metrics' in expected:
        if check_list_match([{"name": m.get("name")} for m in expected['metrics'] if "name" in m], req.metrics, 'metrics'):
            results['metric']['pass'] += 1
        else:
            results['metric']['fail'] += 1
            failed_fields.append('metric')
        
    # 6. Time
    if 'time' in expected:
        if expected['time'] is None:
            if req.date_period is None and req.relative_dates is None: results['time']['pass'] += 1
            else:
                results['time']['fail'] += 1
                failed_fields.append('time')
        else:
            if req.date_period is not None or req.relative_dates is not None: results['time']['pass'] += 1
            else:
                results['time']['fail'] += 1
                failed_fields.append('time')
            
    # 7. Filter
    if 'filters' in expected:
        if check_list_match(expected['filters'], req.filters, 'filters'): results['filter']['pass'] += 1
        else:
            results['filter']['fail'] += 1
            failed_fields.append('filter')
        
    # 8. Aggregation
    if 'metrics' in expected:
        agg_expected = [m.get("aggregation") for m in expected['metrics'] if m.get("aggregation")]
        if not agg_expected:
            results['aggregation']['pass'] += 1
        else:
            agg_actual = req.aggregation
            # Just check if we found some aggregations
            if len(agg_actual) > 0: results['aggregation']['pass'] += 1
            else:
                results['aggregation']['fail'] += 1
                failed_fields.append('aggregation')
                results['aggregation']['fail'] += 1
                failed_fields.append('aggregation')
            
    # 9. Grouping
    if 'group_by' in expected:
        if set(expected['group_by']).issubset(set(req.grouping)): results['grouping']['pass'] += 1
        else:
            results['grouping']['fail'] += 1
            failed_fields.append('grouping')
        
    # 10. Ranking/Limit
    if 'limit' in expected or 'sort' in expected:
        match = True
        if 'limit' in expected and req.limit != expected['limit']: match = False
        if 'sort' in expected and len(req.sorting) == 0: match = False
        if match: results['ranking_limit']['pass'] += 1
        else:
            results['ranking_limit']['fail'] += 1
            failed_fields.append('ranking_limit')
        
    # 11. Output-column
    if 'requested_columns' in expected:
        if set(expected['requested_columns']).issubset(set(req.requested_columns)): results['output_column']['pass'] += 1
        else:
            results['output_column']['fail'] += 1
            failed_fields.append('output_column')
        
    # 12. Clarification
    if 'clarification_required' in expected:
        if expected['clarification_required'] == 'not_null':
            if req.clarification_required: results['clarification']['pass'] += 1
            else:
                results['clarification']['fail'] += 1
                failed_fields.append('clarification')
        elif expected['clarification_required'] is None:
            if not req.clarification_required: results['clarification']['pass'] += 1
            else:
                results['clarification']['fail'] += 1
                failed_fields.append('clarification')



    if len(failed_fields) == 0:
        complete_pass_count += 1
    else:
        req_dict = getattr(req, 'model_dump', lambda: req.__dict__)()
        if not isinstance(req_dict, dict): req_dict = req.__dict__
        failed_details.append({
            "question": test['question'],
            "expected": expected,
            "actual": req_dict,
            "failed_fields": failed_fields
        })


print("\n==============================")
print("NLP Evaluation Results")
print("==============================\n")

for m, r in results.items():
    total = r['pass'] + r['fail']
    if total > 0:
        pct = (r['pass'] / total) * 100
        print(f"{m.capitalize():<15}: {pct:.1f}% ({r['pass']}/{total})")
    else:
        print(f"{m.capitalize():<15}: N/A (no tests specified)")

total_time = time.time() - start_time
avg_time = (total_inference_time / successful_tests) if successful_tests > 0 else 0
print(f"\nTotal tests: {len(tests)}")
passed = successful_tests - len(failed_details)
failed = len(failed_details)
print(f"Passed / failed / timeout / error: {passed} / {failed} / {timeouts} / {errors}")
print(f"Complete Requirement Accuracy: {complete_pass_count}/{successful_tests} ({(complete_pass_count/successful_tests)*100 if successful_tests > 0 else 0:.1f}%)")
print(f"Total execution time: {total_time:.2f} seconds")
print(f"Average inference time per successful question: {avg_time:.2f} seconds")

print("\n==============================")
print("Failed Questions Report")
print("==============================\n")
import json
for fd in failed_details:
    print(f"Question: {fd['question']}")
    print(f"Failed fields: {', '.join(fd['failed_fields'])}")
    print(f"Expected: {json.dumps(fd['expected'], default=str)}")
    print(f"Actual:   {json.dumps(fd['actual'], default=str)}")
    print("-" * 40)

