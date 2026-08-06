import os
import json
import traceback
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List


load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_engine():
    database_url = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME
    )
    return create_engine(database_url)

def safe_execute(conn, query, params=None):
    try:
        if params:
            return conn.execute(text(query), params).fetchall()
        return conn.execute(text(query)).fetchall()
    except SQLAlchemyError as e:
        print(f"Warning: Query execution failed: {e}")
        return []

from app.database.allowed_tables import TARGET_SCOPE_TABLES as TARGET_TABLES

def extract_table_metadata(engine) -> Dict[str, Any]:
    inspector = inspect(engine)
    metadata = {}
    
    with engine.connect() as conn:
        all_tables = inspector.get_table_names()
        
        for table_name in all_tables:
            if table_name not in TARGET_TABLES:
                continue
                
            print(f"Extracting schema and stats for table: {table_name}")
            table_info = {
                "name": table_name,
                "columns": {},
                "primary_keys": inspector.get_pk_constraint(table_name).get('constrained_columns', []),
                "foreign_keys": inspector.get_foreign_keys(table_name),
                "indexes": inspector.get_indexes(table_name),
                "unique_constraints": inspector.get_unique_constraints(table_name),
                "row_count": 0
            }
            
            row_count_res = safe_execute(conn, f"SELECT COUNT(*) FROM `{table_name}`")
            if row_count_res:
                table_info["row_count"] = row_count_res[0][0]
            
            columns = inspector.get_columns(table_name)
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                
                col_info = {
                    "name": col_name,
                    "type": col_type,
                    "nullable": col['nullable'],
                    "default": str(col.get('default')),
                    "comment": col.get('comment', ''),
                    "is_enum": 'ENUM' in col_type.upper(),
                    "enum_values": []
                }
                
                if col_info["is_enum"]:
                    try:
                        enum_str = col_type[col_type.find("(")+1:col_type.rfind(")")]
                        col_info["enum_values"] = [v.strip("'\" ") for v in enum_str.split(",")]
                    except Exception:
                        pass
                
                if table_info["row_count"] > 0 and table_info["row_count"] < 1000000:
                    try:
                        stats = safe_execute(conn, f"""
                            SELECT 
                                COUNT(`{col_name}`) as non_null_count,
                                COUNT(DISTINCT `{col_name}`) as distinct_count
                            FROM `{table_name}`
                        """)
                        if stats:
                            col_info["non_null_count"] = stats[0][0]
                            col_info["distinct_count"] = stats[0][1]
                            col_info["null_count"] = table_info["row_count"] - stats[0][0]
                            
                        if col_info.get("distinct_count", 100) < 50:
                            top_values = safe_execute(conn, f"""
                                SELECT `{col_name}`, COUNT(*) as cnt 
                                FROM `{table_name}` 
                                WHERE `{col_name}` IS NOT NULL
                                GROUP BY `{col_name}` 
                                ORDER BY cnt DESC LIMIT 3
                            """)
                            col_info["top_values"] = [str(val[0]) for val in top_values] if top_values else []
                    except Exception:
                        pass
                
                table_info["columns"][col_name] = col_info
                
            metadata[table_name] = table_info
            
    return metadata

def generate_enterprise_knowledge_base():
    engine = get_engine()
    metadata = extract_table_metadata(engine)
    
    os.makedirs("knowledge/schema", exist_ok=True)
    os.makedirs("knowledge/graph", exist_ok=True)
    
    # 1. schema_metadata.json
    with open("knowledge/schema/schema_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
        
    # 2. entity_dictionary.json
    entity_dict = {}
    with open("knowledge/graph/entity_dictionary.json", "w") as f:
        json.dump(entity_dict, f, indent=4)
        
    # 3. business_dictionary.json
    business_metadata = {
        "business_terminology": {},
        "business_rules": []
    }
    with open("knowledge/graph/business_dictionary.json", "w") as f:
        json.dump(business_metadata, f, indent=4)

    # 4. enum_dictionary.json
    enum_dict = {}
    for table, info in metadata.items():
        for col_name, col_data in info["columns"].items():
            if col_data.get("is_enum") and col_data.get("enum_values"):
                enum_dict[f"{table}.{col_name}"] = col_data["enum_values"]
    with open("knowledge/graph/enum_dictionary.json", "w") as f:
        json.dump(enum_dict, f, indent=4)

    # 5. sample_values.json
    sample_values = {}
    for table, info in metadata.items():
        sample_values[table] = {}
        for col_name, col_data in info["columns"].items():
            if col_data.get("top_values"):
                sample_values[table][col_name] = col_data["top_values"]
    with open("knowledge/graph/sample_values.json", "w") as f:
        json.dump(sample_values, f, indent=4)

    # 6 & 7. relationship_graph.json & join_graph.json
    relationships = []
    join_graph = {"nodes": [], "edges": []}
    for table, info in metadata.items():
        if table not in join_graph["nodes"]:
            join_graph["nodes"].append(table)
        for fk in info.get("foreign_keys", []):
            referred_table = fk.get("referred_table")
            if referred_table in TARGET_TABLES:
                if referred_table not in join_graph["nodes"]:
                    join_graph["nodes"].append(referred_table)
                
                constrained_cols = fk.get("constrained_columns", [])
                referred_cols = fk.get("referred_columns", [])
                
                if len(constrained_cols) > 0 and len(referred_cols) > 0:
                    relationships.append({
                        "from_table": table,
                        "from_column": constrained_cols[0],
                        "to_table": referred_table,
                        "to_column": referred_cols[0],
                        "type": "Many-to-One"
                    })
                    join_graph["edges"].append({
                        "source": table,
                        "target": referred_table,
                        "source_column": constrained_cols[0],
                        "target_column": referred_cols[0]
                    })
    
    with open("knowledge/graph/relationship_graph.json", "w") as f:
        json.dump(relationships, f, indent=4)
        
    with open("knowledge/graph/join_graph.json", "w") as f:
        json.dump(join_graph, f, indent=4)

    # 8. knowledge_graph.json
    knowledge_graph = {
        "nodes": join_graph["nodes"],
        "edges": join_graph["edges"],
        "entities": entity_dict
    }
    with open("knowledge/graph/knowledge_graph.json", "w") as f:
        json.dump(knowledge_graph, f, indent=4)
        
    # 9. query_patterns.json (Seed with requested test queries)
    query_patterns = [
        {"question": "Show first 10 users", "sql": "SELECT id, name, email FROM users LIMIT 10;"},
        {"question": "Show wallet transactions", "sql": "SELECT id, user_id, amount, transaction_type FROM wallet_transaction LIMIT 10;"},
        {"question": "Show companies", "sql": "SELECT id, company_name FROM companies LIMIT 10;"}
    ]
    with open("knowledge/graph/query_patterns.json", "w") as f:
        json.dump(query_patterns, f, indent=4)

    # 10. sql_history_index.json
    with open("knowledge/graph/sql_history_index.json", "w") as f:
        json.dump([], f, indent=4)

    print("\n===================================")
    print("Enterprise Knowledge Base Generated (9 Tables)")
    print("===================================")

if __name__ == "__main__":
    generate_enterprise_knowledge_base()