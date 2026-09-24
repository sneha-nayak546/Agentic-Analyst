import json

with open('scratch/pdf_dump.json', 'r', encoding='utf-8') as f:
    dump = json.load(f)

for p in dump:
    print(f"P{p['page_number']:02d}: tables={len(p['tables'])}")
    for t_idx, t in enumerate(p['tables']):
        rows = t['rows']
        header = rows[0] if rows else []
        print(f"    T{t_idx+1}: {len(rows)} rows, {len(header)} cols: {header[:4]}")
