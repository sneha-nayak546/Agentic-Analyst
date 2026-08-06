import os
import re
import json
from pypdf import PdfReader

from app.database.allowed_tables import ALLOWED_TABLE_NAMES


PDF_PATH = "knowledge/sql_history/sql_history.pdf"

OUTPUT_PATH = "knowledge/generated/sql_history_chunks.json"


print("Reading SQL history PDF...")


reader = PdfReader(PDF_PATH)


full_text = ""


for page_number, page in enumerate(reader.pages):

    print(f"Reading page {page_number + 1}")

    text = page.extract_text()

    if text:
        full_text += text + "\n"



print("\nTotal extracted characters:")
print(len(full_text))


# Save raw extracted text for checking

with open(
    "knowledge/generated/sql_history_raw.txt",
    "w",
    encoding="utf-8"
) as f:

    f.write(full_text)



# Split into SQL chunks

chunks = []


queries = full_text.split(";")


def query_mentions_allowed_table(query: str) -> bool:
    query_lower = query.lower()

    return any(
        re.search(rf"\b{re.escape(table_name)}\b", query_lower)
        for table_name in ALLOWED_TABLE_NAMES
    )


for index, query in enumerate(queries):

    query = query.strip()


    if len(query) > 30 and query_mentions_allowed_table(query):

        chunks.append(
            {
                "id": f"sql_history_{index+1}",

                "type": "sql_example",

                "text": query
            }
        )



os.makedirs(
    "knowledge/generated",
    exist_ok=True
)


with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        chunks,
        f,
        indent=4,
        ensure_ascii=False
    )


print("\n==============================")
print(
    f"Generated SQL chunks: {len(chunks)}"
)
print(
    "Saved:",
    OUTPUT_PATH
)
print("==============================")