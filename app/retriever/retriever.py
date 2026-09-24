import os
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_model = None
_client = None
_collection = None
_schema_meta = None

def get_embedding_model():
    # Return None to use lightning-fast local lexical retrieval without heavy PyTorch overhead
    return None

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

    # Level 1: Semantic Vector Search on table descriptions to identify candidate tables across all 238 tables
    collection = get_chroma_collection()
    if collection:
        try:
            res = collection.query(query_texts=[question], n_results=k)
            if res and res.get("metadatas") and res["metadatas"][0]:
                for meta in res["metadatas"][0]:
                    if "table_name" in meta:
                        detected_tables.add(meta["table_name"])
        except Exception as e:
            logger.warning(f"[RAG WARNING] ChromaDB query failed: {e}")

    # Lexical Concept Mapping across all known tables
    q_lower = question.lower()
    schema = get_schema_metadata()

    # Direct entity and keyword table linking using Business Semantic Metadata
    try:
        from app.knowledge.semantic_metadata import BUSINESS_SEMANTIC_METADATA
        for tbl_name, t_meta in BUSINESS_SEMANTIC_METADATA.items():
            # Check table description and synonyms
            if any(syn in q_lower for syn in [tbl_name, tbl_name.replace("_", " "), t_meta.get("entity_type", "")]):
                detected_tables.add(tbl_name)
            # Check column-level synonyms
            for c_name, c_info in t_meta.get("columns", {}).items():
                synonyms = c_info.get("synonyms", [])
                if any(re.search(rf"\b{re.escape(syn)}\b", q_lower) for syn in synonyms):
                    detected_tables.add(tbl_name)
    except Exception as e:
        logger.warning(f"[RAG WARNING] Semantic metadata retrieval failed: {e}")

    # Fallback / Comprehensive Concept Mapping across all known tables
    TABLE_KEYWORDS = {
        "users": ["user", "users", "retailer", "retailers", "distributor", "distributors", "wholesaler", "wholesalers", "mechanic", "mechanics", "state", "states", "city", "bengaluru", "mysuru", "karnataka", "maharashtra", "kerala", "pune", "mumbai"],
        "retailer_distributor_mappings": ["their retailers", "linked retailers", "linked to distributor", "retailers linked", "distributor retailer", "distributor mappings", "distributor's retailers", "retailers associated", "retailer under distributor", "retailers under"],
        "wallet_transaction": ["wallet", "transaction", "transactions", "earning", "earnings", "topup", "topups", "balance", "credit", "debit", "cash point"],
        "withdrawal_request": ["withdrawal", "withdrawals", "payout", "payouts", "approved ones", "pending ones", "rejected ones"],
        "sku_inventories": ["sku", "inventory", "inventories", "stock", "box", "boxes", "scan", "scans", "box scan", "box scans", "scanned box", "scanned boxes", "category", "categories", "dispatches", "uom"],
        "qr_point_map": ["qr_point_map", "box_calulation_um", "qr", "points", "box scan", "box scans", "scanned boxes", "boxes scanned", "scanned box", "boxes", "scan", "scanning"],
        "state": ["state", "states", "karnataka", "maharashtra", "tamil nadu", "kerala", "gujarat"],
        "companies": ["company", "companies", "client", "clients"],
        "role": ["role", "roles", "user role", "permissions"]
    }

    for tbl, kws in TABLE_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", q_lower) for kw in kws):
            detected_tables.add(tbl)

    # Disambiguation: Box scans vs Wallet Transactions
    # If question asks about box scans and does NOT mention wallet/earnings/cashback/withdrawal, discard wallet_transaction
    has_box_scan = any(re.search(rf"\b{re.escape(kw)}\b", q_lower) for kw in ["box scan", "box scans", "scanned box", "scanned boxes", "boxes scanned", "scanned", "scan", "boxes", "box"])
    has_wallet_terms = any(re.search(rf"\b{re.escape(kw)}\b", q_lower) for kw in ["wallet", "earning", "earnings", "cash", "transaction", "balance", "credit", "debit", "withdrawal"])
    if has_box_scan and not has_wallet_terms:
        detected_tables.discard("wallet_transaction")
        detected_tables.add("sku_inventories")
        detected_tables.add("qr_point_map")

    # If still no tables detected, attempt schema expansion across all table and column names
    if not detected_tables:
        q_words = set(re.findall(r"\w+", q_lower))
        for tbl, tbl_meta in schema.items():
            tbl_clean = tbl.lower().replace("_", " ")
            if any(w in tbl_clean for w in q_words if len(w) > 3):
                detected_tables.add(tbl)
            else:
                cols = tbl_meta.get("columns", {})
                col_names = [c.get("name", "").lower() for c in (cols.values() if isinstance(cols, dict) else cols)]
                if any(w in col_names for w in q_words if len(w) > 3):
                    detected_tables.add(tbl)

    # Connectivity expansion: If sku_inventories is detected, always include qr_point_map and users
    if "sku_inventories" in detected_tables:
        detected_tables.add("qr_point_map")
        detected_tables.add("users")
        if any(w in q_lower for w in ["state", "states", "region"]):
            detected_tables.add("state")
        if any(w in q_lower for w in ["retailer", "retailers", "under distributor", "distributor"]):
            detected_tables.add("retailer_distributor_mappings")

    # If wallet_transaction is detected, include users
    if "wallet_transaction" in detected_tables:
        detected_tables.add("users")

    # If withdrawal_request is detected, include users and wallet_transaction
    if "withdrawal_request" in detected_tables:
        detected_tables.add("users")
        detected_tables.add("wallet_transaction")

    # Filter candidate tables strictly against actual discovered schema
    if schema:
        detected_tables = {t for t in detected_tables if t in schema}

    # Safe Handling: If STILL nothing found after expansion, fallback to users table
    if not detected_tables:
        detected_tables.add("users")

    # Cap to top 15 candidate tables
    candidate_list = sorted(list(detected_tables))[:15]

    from app.knowledge.table_schemas import get_selective_schema_context
    return get_selective_schema_context(candidate_list)


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