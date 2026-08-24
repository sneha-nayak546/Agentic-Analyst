import json
from typing import Dict, Any, Optional
from app.retriever.retriever import retrieve_sql_history
from app.knowledge.table_schemas import get_selective_schema_context
from app.knowledge.business_rule_index import get_selective_business_rules

def build_sql_prompt(execution_plan_json: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Selective Semantic Prompt Builder.
    Constructs a compact, clearly sectioned prompt containing ONLY the schema,
    business rules, and examples relevant to the current user query.
    Separates the raw user question from context, filters, and schema.
    """
    if isinstance(execution_plan_json, dict):
        plan = execution_plan_json
    else:
        try:
            plan = json.loads(execution_plan_json)
        except Exception:
            plan = {}

    ctx = context or {}
    intent = plan.get("intent", "")
    tables = plan.get("tables", ["users"])
    if not tables:
        tables = ["users"]

    # 1. Structured Filter Breakdown
    filters_lines = []
    entity = plan.get("primary_entity") or "none"
    role_id = plan.get("role_id")
    if role_id:
        filters_lines.append(f"entity = {entity} (user_role = {role_id})")
    else:
        filters_lines.append(f"entity = {entity}")

    specific_id = plan.get("specific_id")
    if specific_id:
        id_type = plan.get("id_type")
        if id_type and id_type != entity:
            if id_type == "distributor":
                filters_lines.append(f"SQL FILTER REQUIRED: users.distributer_id = {specific_id}")
            else:
                filters_lines.append(f"SQL FILTER REQUIRED: linked_{id_type}_id = {specific_id}")
        else:
            filters_lines.append(f"SQL FILTER REQUIRED: users.id = {specific_id}")

    region = plan.get("region")
    filters_lines.append(f"location/region = {region if region else 'none'}")

    time_filter = plan.get("time_filter")
    filters_lines.append(f"date/time = {time_filter if (time_filter and time_filter != 'None') else 'none'}")

    status_filter = plan.get("status_filter")
    if status_filter:
        filters_lines.append(f"status = {status_filter}")

    metric = "earnings" if plan.get("is_earnings_query") else ("balance" if "balance" in intent.lower() else "none")
    filters_lines.append(f"metric = {metric}")

    filters_str = "\n".join([f"- {fl}" for fl in filters_lines])

    # 1.5 Structural Requirements
    struct_lines = []
    output_format = plan.get("output_format")
    if output_format:
        struct_lines.append(f"output_format = {output_format}")
    
    req_cols = plan.get("required_columns")
    if req_cols:
        struct_lines.append(f"required_columns = {', '.join(req_cols)}")
        
    target_measures = plan.get("target_measures")
    if target_measures:
        struct_lines.append(f"target_measures_and_aggregations = {', '.join(target_measures)}")
        
    group_by = plan.get("group_by")
    if group_by:
        struct_lines.append(f"group_by = {', '.join(group_by)}")
        
    order_by = plan.get("order_by")
    if order_by:
        struct_lines.append(f"order_by = {', '.join(order_by)}")
        
    struct_str = "\n".join([f"- {sl}" for sl in struct_lines]) if struct_lines else "None"

    # 2. Selective Schema (Target tables only)
    selective_schema = get_selective_schema_context(tables)

    # 3. Selective Business Rules & Term Mappings
    selective_rules = get_selective_business_rules(tables, intent)

    # 4. Relevant Few-Shot Examples (Filtered to current intent)
    exemplars_text = retrieve_sql_history(intent, k=2)

    # 5. Follow-Up Context (ONLY if genuine follow-up)
    follow_up_section = ""
    is_follow_up = ctx.get("is_explicit_follow_up", False) or plan.get("is_explicit_follow_up", False)
    if is_follow_up:
        inherited_items = []
        if ctx.get("region"):
            inherited_items.append(f"Inherited Region: {ctx['region']}")
        if ctx.get("entity"):
            inherited_items.append(f"Inherited Entity: {ctx['entity']}")
        if ctx.get("period"):
            inherited_items.append(f"Inherited Period: {ctx['period']}")
        if inherited_items:
            follow_up_section = "\nFOLLOW-UP CONTEXT (Active Conversation):\n" + "\n".join([f"- {it}" for it in inherited_items]) + "\n"

    # Assemble sectioned prompt
    sections = [
        "You are an expert MySQL Data Analyst for JGH Enterprise.",
        "Your task is to write an optimized MySQL SELECT query to answer the user question using ONLY the provided schema and business rules.\n",
        f"CURRENT USER QUESTION:\n\"{intent}\"\n",
        f"CURRENT EXPLICIT FILTERS:\n{filters_str}\n",
        f"STRUCTURAL REQUIREMENTS:\n{struct_str}\n"
    ]

    if follow_up_section:
        sections.append(follow_up_section)

    sections.append(f"RELEVANT SCHEMA:\n{selective_schema}\n")

    if selective_rules:
        sections.append(f"RELEVANT BUSINESS RULES & MAPPINGS:\n{selective_rules}\n")

    if exemplars_text:
        sections.append(f"RELEVANT EXAMPLES:\n{exemplars_text}\n")

    sections.append(
        "CRITICAL RULES:\n"
        "1. Write ONLY a valid MySQL SELECT query inside a ```sql ``` code block.\n"
        "2. Do NOT hallucinate table or column names not listed in RELEVANT SCHEMA.\n"
        "3. Do NOT add location/region or date filters unless explicitly listed in CURRENT EXPLICIT FILTERS.\n"
        "4. Output only the query.\n"
        "5. You MUST include ALL CURRENT EXPLICIT FILTERS (like specific_id, linked_id, entity, date/time) in your WHERE clause if they are not 'none'.\n"
        "6. You MUST satisfy ALL STRUCTURAL REQUIREMENTS (group_by, order_by, required_columns, output_format, target_measures_and_aggregations) in your query.\n"
        "7. NEVER ignore 'SQL FILTER REQUIRED' directives. They must be exactly applied as written."
    )

    return "\n".join(sections).strip()