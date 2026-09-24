import os
import json
from functools import lru_cache

_model = None
_client = None
_collection = None
_schema_meta = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            return None
    return _model

def get_chroma_collection():
    global _client, _collection
    if _client is None:
        try:
            import chromadb
            db_path = "knowledge/chroma_db"
            if not os.path.exists(db_path):
                return None
            _client = chromadb.PersistentClient(path=db_path)
            try:
                _collection = _client.get_collection("enterprise_schema")
            except Exception:
                return None
        except ImportError:
            return None
    return _collection

def get_schema_metadata():
    global _schema_meta
    if _schema_meta is None:
        schema_file = "knowledge/schema/schema_metadata.json"
        if os.path.exists(schema_file):
            with open(schema_file, "r", encoding="utf-8") as f:
                _schema_meta = json.load(f)
        else:
            _schema_meta = {}
    return _schema_meta

@lru_cache(maxsize=256)
def retrieve_schema(question: str, k: int = 1) -> str:
    """
    Hybrid semantic retrieval:
    1. Resolve intent via Knowledge Graph (graph + metadata)
    2. Retrieve additional context via ChromaDB Vector Search (top K=1 to minimize context)
    3. Merge into COMPRESSED LLM context.
    """
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    
    # 1. Graph Resolution
    resolution = kg.resolve_business_query(question)
    detected_tables = set(resolution["detected_tables"])
    
    # 2. Vector Search (fallback only if no tables found or just top 1)
    if len(detected_tables) == 0:
        collection = get_chroma_collection()
        model = get_embedding_model()
        
        if collection and model:
            try:
                emb = model.encode(question).tolist()
                res = collection.query(query_embeddings=[emb], n_results=k)
                if res and res["metadatas"] and res["metadatas"][0]:
                    for meta in res["metadatas"][0]:
                        if "table_name" in meta:
                            detected_tables.add(meta["table_name"])
            except Exception as e:
                pass

    # 3. Assemble COMPACT Context
    lines = []
    schema = get_schema_metadata()
    
    for tbl in detected_tables:
        if tbl in schema:
            info = schema[tbl]
            col_list = []
            enum_list = []
            cols = info.get("columns", {})
            cols_iterable = cols.values() if isinstance(cols, dict) else (cols if isinstance(cols, list) else [])
            for col_data in cols_iterable:
                col_name = col_data.get("name", "")
                col_list.append(col_name)
                if col_data.get("is_enum") and col_data.get("enum_values"):
                    enum_list.append(f"{col_name}({','.join(col_data['enum_values'])})")
            
            tbl_def = f"Table `{tbl}`:\n  Columns: {', '.join(col_list)}"
            if enum_list:
                tbl_def += f"\n  Enums: {'; '.join(enum_list)}"
            lines.append(tbl_def)
        
    # Include Graph logic
    if resolution["detected_joins"]:
        lines.append("Joins:\n" + "\n".join([f"- {j}" for j in resolution["detected_joins"]]))
        
    if resolution["date_range"]:
        lines.append(f"Date Filter: {resolution['date_range']['start']} to {resolution['date_range']['end']}")

    if not lines:
        return "No schema context found."
        
    return "\n\n".join(lines)

import re

@lru_cache(maxsize=128)
def retrieve_sql_history(question: str, k: int = 2) -> str:
    """
    Retrieves the top k most relevant gold-standard question-to-SQL exemplars
    from query_patterns.json using semantic vector embeddings and keyword boosts.
    """
    pattern_files = ["knowledge/patterns/query_patterns.json", "knowledge/graph/query_patterns.json"]
    patterns = []
    for p_path in pattern_files:
        if os.path.exists(p_path):
            try:
                with open(p_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        patterns.extend(data)
                    elif isinstance(data, dict) and "patterns" in data:
                        patterns.extend(data["patterns"])
            except Exception:
                pass

    if not patterns:
        return ""

    model = get_embedding_model()
    
    scored_exemplars = []
    
    if model:
        try:
            from sentence_transformers import util
            q_emb = model.encode(question)
            
            for item in patterns:
                ex_q = item.get("question") or item.get("intent", "")
                ex_sql = item.get("sql") or item.get("pattern", "")
                if not ex_q or not ex_sql:
                    continue
                    
                ex_emb = model.encode(ex_q)
                base_score = util.cos_sim(q_emb, ex_emb).item()
                
                boost = 0.0
                q_lower = question.lower()
                ex_q_lower = ex_q.lower()
                
                # Hybrid Boosts
                if any(w in q_lower for w in ["retailer", "retailers"]) and any(w in ex_q_lower for w in ["retailer", "retailers"]):
                    boost += 0.2
                if any(w in q_lower for w in ["earning", "earnings"]) and any(w in ex_q_lower for w in ["earning", "earnings"]):
                    boost += 0.2
                if any(w in q_lower for w in ["month", "july"]) and any(w in ex_q_lower for w in ["month", "july"]):
                    boost += 0.1
                
                final_score = base_score + boost
                scored_exemplars.append((final_score, ex_q, ex_sql))
        except Exception as e:
            # Fallback if sentence transformers crashes
            model = None
            
    # Fallback to word overlap if model failed or missing
    if not model:
        q_words = set(re.findall(r"\w+", question.lower()))
        for item in patterns:
            ex_q = item.get("question") or item.get("intent", "")
            ex_sql = item.get("sql") or item.get("pattern", "")
            if not ex_q or not ex_sql:
                continue
                
            ex_words = set(re.findall(r"\w+", ex_q.lower()))
            overlap = len(q_words.intersection(ex_words))
            
            boost = 0
            if any(w in question.lower() for w in ["retailer", "retailers"]) and any(w in ex_q.lower() for w in ["retailer", "retailers"]):
                boost += 2
            if any(w in question.lower() for w in ["earning", "earnings"]) and any(w in ex_q.lower() for w in ["earning", "earnings"]):
                boost += 2
            if any(w in question.lower() for w in ["month", "july"]) and any(w in ex_q.lower() for w in ["month", "july"]):
                boost += 1

            score = overlap + boost
            scored_exemplars.append((score, ex_q, ex_sql))

    scored_exemplars.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored_exemplars[:k]

    if not top_matches:
        return ""

    formatted_examples = []
    for idx, (score, ex_q, ex_sql) in enumerate(top_matches, 1):
        formatted_examples.append(f"Example {idx}:\nQuestion: {ex_q}\nSQL:\n{ex_sql}")

    return "\n\n".join(formatted_examples)