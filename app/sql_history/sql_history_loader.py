import os
import json
from pypdf import PdfReader



PDF_PATH = "knowledge/sql_history/sql_history.pdf"

OUTPUT_PATH = "knowledge/generated/sql_history_chunks.json"



def extract_pdf_text():


    print("Reading SQL history PDF...")


    reader = PdfReader(
        PDF_PATH
    )


    text = ""


    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"



    return text




def create_chunks(text):


    print("Creating SQL knowledge chunks...")


    chunks=[]


    parts=text.split(
        "SELECT"
    )


    index=1


    for part in parts[1:]:


        sql = "SELECT" + part


        chunks.append(
            {
                "id":
                f"sql_history_{index}",

                "type":
                "sql_example",

                "text":
                sql[:2000]
            }
        )


        index+=1



    return chunks




def save_chunks(chunks):


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
            indent=4
        )



    print(
        f"Created {len(chunks)} SQL examples"
    )





if __name__=="__main__":


    text = extract_pdf_text()


    chunks = create_chunks(
        text
    )


    save_chunks(
        chunks
    )


    print("Completed")