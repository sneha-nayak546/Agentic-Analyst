import pymupdf
import json

doc = pymupdf.open('JGH_Intelligence_Engine_Report.pdf')
pages_data = []

for i, page in enumerate(doc):
    p_info = {
        "page_number": i + 1,
        "rect": list(page.rect),
        "text": page.get_text(),
        "tables": []
    }
    tabs = page.find_tables()
    for t in tabs.tables:
        p_info["tables"].append({
            "bbox": list(t.bbox),
            "rows": t.extract()
        })
    pages_data.append(p_info)

with open('scratch/pdf_dump.json', 'w', encoding='utf-8') as f:
    json.dump(pages_data, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(pages_data)} pages to scratch/pdf_dump.json")
