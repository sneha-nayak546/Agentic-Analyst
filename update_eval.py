import re

with open('evaluate_nlp.py', 'r') as f:
    content = f.read()

# 1. Add complete_pass_count and failed_details variables
content = content.replace(
    "total_inference_time = 0.0\nsuccessful_tests = 0\n",
    "total_inference_time = 0.0\nsuccessful_tests = 0\ntimeouts = 0\nerrors = 0\ncomplete_pass_count = 0\nfailed_details = []\n"
)

# 2. Update the exception handlers
content = content.replace(
    "print(f\"TIMEOUT: Test {i+1} took longer than 45 seconds.\")\n        continue",
    "print(f\"TIMEOUT: Test {i+1} took longer than 45 seconds.\")\n        timeouts += 1\n        continue"
)
content = content.replace(
    "print(f\"ERROR: Test {i+1} failed with exception: {e}\")\n        continue",
    "print(f\"ERROR: Test {i+1} failed with exception: {e}\")\n        errors += 1\n        continue"
)

# 3. Add failed_fields initialization
content = content.replace(
    "expected = test['expected']\n    \n    # 1. Intent",
    "expected = test['expected']\n    \n    failed_fields = []\n    \n    # 1. Intent"
)

# 4. Update the 12 checks to append to failed_fields
metrics = [
    ("intent", "'intent'"),
    ("entity", "'entities'"),
    ("relationship", "'relationships'"),
    ("id", "'specific_ids'"),
    ("metric", "'metrics'"),
    ("time", "'time'"),
    ("filter", "'filters'"),
    ("aggregation", "'metrics'"),
    ("grouping", "'group_by'"),
    ("ranking_limit", "('limit' in expected or 'sort' in expected)"),
    ("output_column", "'requested_columns'"),
    ("clarification", "'clarification_required'")
]

for m_name, _ in metrics:
    # We find: else: results['metric_name']['fail'] += 1
    old_fail = f"else: results['{m_name}']['fail'] += 1"
    new_fail = f"else:\n            results['{m_name}']['fail'] += 1\n            failed_fields.append('{m_name}')"
    content = content.replace(old_fail, new_fail)

# 5. Add the complete pass check at the end of the loop
end_of_loop_marker = "            else: results['clarification']['fail'] += 1\n            failed_fields.append('clarification')"

end_of_loop = """
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
"""
# We will inject this before the final print statement
content = content.replace("print(\"\\n==============================\")", end_of_loop + "\n\nprint(\"\\n==============================\")")


# 6. Update the final print to include the requested report format
final_print_old = """total_time = time.time() - start_time
avg_time = (total_inference_time / successful_tests) if successful_tests > 0 else 0
print(f"\\nTotal tests run: {len(tests)}")
print(f"Successful completions: {successful_tests}")
print(f"Total execution time: {total_time:.2f} seconds")
print(f"Average inference time per successful question: {avg_time:.2f} seconds")"""

final_print_new = """total_time = time.time() - start_time
avg_time = (total_inference_time / successful_tests) if successful_tests > 0 else 0
print(f"\\nTotal tests: {len(tests)}")
passed = successful_tests - len(failed_details)
failed = len(failed_details)
print(f"Passed / failed / timeout / error: {passed} / {failed} / {timeouts} / {errors}")
print(f"Complete Requirement Accuracy: {complete_pass_count}/{successful_tests} ({(complete_pass_count/successful_tests)*100 if successful_tests > 0 else 0:.1f}%)")
print(f"Total execution time: {total_time:.2f} seconds")
print(f"Average inference time per successful question: {avg_time:.2f} seconds")

print("\\n==============================")
print("Failed Questions Report")
print("==============================\\n")
import json
for fd in failed_details:
    print(f"Question: {fd['question']}")
    print(f"Failed fields: {', '.join(fd['failed_fields'])}")
    print(f"Expected: {json.dumps(fd['expected'], default=str)}")
    print(f"Actual:   {json.dumps(fd['actual'], default=str)}")
    print("-" * 40)
"""

content = content.replace(final_print_old, final_print_new)

with open('evaluate_nlp.py', 'w') as f:
    f.write(content)

print("Updated evaluate_nlp.py")
