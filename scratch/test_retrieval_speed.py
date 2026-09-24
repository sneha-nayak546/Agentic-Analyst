import time
import chromadb

client = chromadb.PersistentClient(path='knowledge/chroma_db')
col = client.get_collection('enterprise_schema')
for q in [
    'List retailers associated with distributor 7001',
    'Show top 5 retailers by earnings in August 2026',
    'Give me transaction totals grouped by month',
    'Show withdrawal requests for August'
]:
    t0 = time.time()
    res = col.query(query_texts=[q], n_results=5)
    tables = [m.get('table_name') for m in res['metadatas'][0]]
    print(f"Q: '{q}' -> {time.time()-t0:.3f}s: {tables}")
