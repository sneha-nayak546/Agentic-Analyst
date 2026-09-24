import json

with open('tests/comprehensive_200_accuracy_benchmark.json', 'r', encoding='utf-8') as f:
    bench = json.load(f)

for q_id in [17, 33, 61, 69, 85, 105, 125, 131, 145, 153, 159, 167, 177, 185, 191, 197, 205]:
    item = next((c for c in bench if c['id'] == q_id), None)
    if item:
        print(f"ID {q_id}: exp_lim={item.get('expected_limit')}, exp_rows={item.get('expected_row_count')}, cat={item.get('category')}")
        print(f"   Ref SQL: {item.get('reference_sql')}")
