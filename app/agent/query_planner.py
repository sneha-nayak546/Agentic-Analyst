import json
from app.knowledge.knowledge_graph import get_knowledge_graph

class QueryPlanner:
    def __init__(self):
        self.kg = get_knowledge_graph()

    def build_execution_plan(self, question: str) -> dict:
        """
        Deterministically builds an execution plan from the question using in-memory metadata.
        This structured plan acts as the blueprint for the LLM to write SQL.
        """
        # 1. Resolve tables and joins from the knowledge graph
        resolution = self.kg.resolve_business_query(question)
        
        detected_tables = resolution.get("detected_tables", [])
        detected_joins = resolution.get("detected_joins", [])
        date_range = resolution.get("date_range", None)
        
        # 2. Identify rich schema details for the detected tables
        schema_details = {}
        for tbl in detected_tables:
            tbl_info = self.kg.schema_meta.get(tbl, {})
            cols = []
            for col_data in tbl_info.get("columns", {}).values():
                col_name = col_data.get("name")
                if not col_name: continue
                
                col_type = col_data.get("type", "")
                details = f"{col_name} ({col_type})"
                
                if col_name in tbl_info.get("primary_keys", []):
                    details += " PRIMARY KEY"
                    
                if col_data.get("is_enum"):
                    enums = col_data.get("enum_values", [])
                    details += f" ENUM: [{', '.join(enums)}]"
                
                if col_data.get("top_values"):
                    details += f" Samples: {col_data['top_values']}"
                    
                cols.append(details)
            schema_details[tbl] = cols

        # 3. Identify Business Terms (from business_dictionary.json if any)
        business_terms = []
        for term, mapping in self.kg.business_meta.get("business_terminology", {}).items():
            if term.lower() in question.lower():
                business_terms.append({term: mapping})

        # 4. Construct Execution Plan
        execution_plan = {
            "intent": question,
            "business_terms": business_terms,
            "tables": detected_tables,
            "schema_details": schema_details,
            "relationships_required": detected_joins,
            "date_filters": date_range,
            "rules": [
                "NEVER use SELECT *.",
                "ALWAYS apply LIMIT 500 unless specifically asked for more.",
                "USE explicitly provided joins.",
                "If computing aggregates, use GROUP BY."
            ]
        }
        
        return execution_plan

def create_plan(question: str) -> dict:
    planner = QueryPlanner()
    return planner.build_execution_plan(question)
