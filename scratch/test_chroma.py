import chromadb

client = chromadb.PersistentClient(path='knowledge/chroma_db')
for c_name in ['enterprise_schema', 'database_knowledge', 'sql_knowledge', 'sql_history']:
    try:
        col = client.get_collection(c_name)
        print(f"\nCollection '{c_name}' (count: {col.count()}):")
        # Peek at first 2 items
        peek = col.peek(limit=2)
        for i in range(len(peek['ids'])):
            print(f"  ID: {peek['ids'][i]}")
            print(f"  Meta: {peek['metadatas'][i]}")
            print(f"  Doc: {peek['documents'][i][:120]}...\n")
        
        # Test query_texts
        res = col.query(query_texts=["wallet transactions and distributor earnings"], n_results=2)
        print(f"  Query text match: {res['ids'][0]}")
    except Exception as e:
        print(f"  Error on {c_name}: {e}")
