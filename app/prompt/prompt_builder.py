import json
from typing import Dict, Any, Optional
from app.retriever.retriever import retrieve_sql_history
from app.knowledge.table_schemas import get_selective_schema_context
from app.knowledge.business_rule_index import get_selective_business_rules
from app.agent.execution_plan import ExecutionPlan

def build_sql_prompt(plan: ExecutionPlan, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Selective Semantic Prompt Builder.
    Constructs a compact, clearly sectioned prompt containing ONLY the schema,
    business rules, and examples relevant to the current user query.
    Separates the raw user question from context, filters, and schema.
    """
    ctx = context or {}
    req = plan.business_requirement
    intent = req.intent
    original_question = req.original_question
    tables = plan.relevant_tables
    
    if not tables:
        tables = ["users"]

    # 1. Structured Filter Breakdown
    filters_lines = []
    if req.entities:
        filters_lines.append(f"entities = {', '.join(req.entities)}")
        
    for k, v in req.specific_ids.items():
        filters_lines.append(f"SQL FILTER REQUIRED: specific_id {k} = {v}")

    for f in req.filters:
        filters_lines.append(f"filter: {f}")

    if req.date_period or req.relative_dates:
        filters_lines.append(f"date/time = {req.date_period or req.relative_dates}")

    if req.metrics:
        filters_lines.append(f"metrics = {', '.join(req.metrics)}")

    filters_str = "\n".join([f"- {fl}" for fl in filters_lines]) if filters_lines else "None"

    # 1.5 Structural Requirements
    struct_lines = []
    if req.output_format:
        struct_lines.append(f"output_format = {req.output_format}")
    if req.requested_columns:
        struct_lines.append(f"required_columns = {', '.join(req.requested_columns)}")
    if req.aggregation:
        struct_lines.append(f"aggregations = {', '.join(req.aggregation)}")
    if req.grouping:
        struct_lines.append(f"group_by = {', '.join(req.grouping)}")
    if req.sorting:
        struct_lines.append(f"order_by = {', '.join(req.sorting)}")
    if req.limit:
        struct_lines.append(f"limit = {req.limit}")
    if plan.required_joins:
        struct_lines.append(f"required_joins = {', '.join(plan.required_joins)}")
        
    struct_str = "\n".join([f"- {sl}" for sl in struct_lines]) if struct_lines else "None"

    # 2. Selective Schema (Target tables only)
    selective_schema = get_selective_schema_context(tables)

    # 3. Selective Business Rules & Term Mappings
    selective_rules = get_selective_business_rules(tables, intent)

    # 4. Relevant Few-Shot Examples (Filtered to current intent)
    exemplars_text = retrieve_sql_history(intent, k=2)

    # 5. Follow-Up Context (ONLY if genuine follow-up)
    follow_up_section = ""
    if ctx:
        follow_up_section = "\nFOLLOW-UP CONTEXT (Active Conversation):\n" + json.dumps(ctx, indent=2) + "\n"

    # Assemble sectioned prompt for maximum vLLM prefix cache hit rate.
    # Static rules and schema come first, dynamic queries come last.
    sections = [
        "You are an expert MySQL Data Analyst for JGH Enterprise.",
        "Your task is to write an optimized MySQL SELECT query to answer the user question using ONLY the provided schema and business rules.\n",
        "CRITICAL RULES:\n"
        "1. Write ONLY a valid MySQL SELECT query inside a ```sql ``` code block.\n"
        "2. Do NOT hallucinate table or column names not listed in RELEVANT SCHEMA.\n"
        "3. Output only the query.\n"
        "4. You MUST include ALL CURRENT EXPLICIT FILTERS in your WHERE clause if they are not 'none'.\n"
        "5. You MUST satisfy ALL STRUCTURAL REQUIREMENTS (group_by, order_by, required_columns, output_format, aggregations) in your query.\n"
        "6. NEVER ignore 'SQL FILTER REQUIRED' directives. They must be exactly applied as written.\n"
    ]

    sections.append(f"RELEVANT SCHEMA:\n{selective_schema}\n")

    if selective_rules:
        sections.append(f"RELEVANT BUSINESS RULES & MAPPINGS:\n{selective_rules}\n")

    if exemplars_text:
        sections.append(f"RELEVANT EXAMPLES:\n{exemplars_text}\n")
        
    if plan.rag_evidence:
        sections.append(f"RELATIONSHIP RESOLVER EVIDENCE:\n{plan.rag_evidence}\n")

    if follow_up_section:
        sections.append(follow_up_section)

    sections.append(f"CURRENT EXPLICIT FILTERS:\n{filters_str}\n")
    sections.append(f"STRUCTURAL REQUIREMENTS:\n{struct_str}\n")
    sections.append(f"CURRENT USER QUESTION:\n\"{original_question}\"\n")

    return "\n".join(sections).strip()