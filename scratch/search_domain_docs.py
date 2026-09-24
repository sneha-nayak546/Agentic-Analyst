import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

files = [
    "knowledge/Business_Executive_Scenarios_Specification.md",
    "knowledge/Enterprise_Architectural_Scenarios_Specification.md",
    "knowledge/business_dictionary.json",
    "knowledge/business_metadata.json",
    "knowledge/draft_db_profile.json",
    "knowledge/relationships/relationships.json"
]

keywords = ["box scan", "scanned box", "box", "scan", "category", "uom", "sku_inventories", "lpn"]

for fpath in files:
    if not os.path.exists(fpath):
        continue
    print(f"\n=================== {fpath} ===================")
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    for kw in keywords:
        matches = [m.start() for m in re.finditer(re.escape(kw), content, re.IGNORECASE)]
        if matches:
            print(f"  Keyword '{kw}': {len(matches)} occurrences")
            for pos in matches[:3]:
                start = max(0, pos - 100)
                end = min(len(content), pos + 150)
                snippet = content[start:end].replace("\n", " ")
                print(f"    ... {snippet} ...")
