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
            _model = None
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
def retrieve_schema(question: str, k: int = 5) -> str:
    """
    Hierarchical Semantic RAG Retrieval:
    Level 1: Semantic Vector Search on table descriptions to identify candidate tables.
    Level 2: Extract full columns & enum definitions only for top K candidates.
    Level 3: Extract relevant Foreign Key relationships for candidate tables.
    """
    detected_tables = set()
    
    # Try NLP Knowledge Graph first for explicit exact matches
    try:
        from app.knowledge.knowledge_graph import get_knowledge_graph
        kg = get_knowledge_graph()
        resolution = kg.resolve_business_query(question)
        if resolution and resolution.get("detected_tables"):
            detected_tables.update(resolution["detected_tables"])
    except:
        pass

    # Level 1: Vector Search for Candidate Tables
    collection = get_chroma_collection()
    model = get_embedding_model()
    
    if collection and model:
        try:
            emb = model.encode(question).tolist()
            res = collection.query(query_embeddings=[emb], n_results=k)
            if res and res.get("metadatas") and res["metadatas"][0]:
                for meta in res["metadatas"][0]:
                    if "table_name" in meta:
                        detected_tables.add(meta["table_name"])
        except Exception as e:
            print(f"[RAG WARNING] ChromaDB query failed: {e}")

    # Fallback to defaults if nothing found
    if not detected_tables:
        detected_tables = {"users", "wallet_transaction", "role"}

    # Level 2 & 3: Assemble COMPACT Context (Only for Candidate Tables)
    lines = []
    schema = get_schema_metadata()
    
    for tbl in detected_tables:
        if tbl in schema:
            info = schema[tbl]
            col_list = []
            enum_list = []
            fk_list = []
            
            cols = info.get("columns", {})
            cols_iterable = cols.values() if isinstance(cols, dict) else (cols if isinstance(cols, list) else [])
            for col_data in cols_iterable:
                col_name = col_data.get("name", "")
                c_type = col_data.get("datatype", "")
                col_list.append(f"{col_name} ({c_type})")
                
                if col_data.get("is_enum") and col_data.get("enum_values"):
                    enum_list.append(f"{col_name} IN ({','.join(col_data['enum_values'])})")
                    
                if col_data.get("foreign_key"):
                    fk_tbl = col_data["foreign_key"].get("table")
                    fk_col = col_data["foreign_key"].get("column")
                    if fk_tbl in detected_tables: # Only show relationships to other retrieved tables
                        fk_list.append(f"JOIN {fk_tbl} ON {tbl}.{col_name} = {fk_tbl}.{fk_col}")
            
            tbl_def = f"Table `{tbl}`:\n  Columns: {', '.join(col_list)}"
            if info.get("comment"):
                tbl_def += f"\n  Desc: {info['comment']}"
            if enum_list:
                tbl_def += f"\n  Enums: {'; '.join(enum_list)}"
            if fk_list:
                tbl_def += f"\n  Relationships: {'; '.join(fk_list)}"
            lines.append(tbl_def)
        
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