from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.agent.business_requirement import BusinessRequirement

class ExecutionPlan(BaseModel):
    """
    Canonical Execution Plan.
    Acts as the grounding contract for SQL generation based on the BusinessRequirement,
    resolved entities, schema context, and verified relationships.
    """
    business_requirement: BusinessRequirement
    resolved_entities: List[str] = Field(default_factory=list)
    resolved_relationships: List[str] = Field(default_factory=list)
    relevant_tables: List[str] = Field(default_factory=list)
    relevant_columns: List[str] = Field(default_factory=list)
    required_joins: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)
    grouping: List[str] = Field(default_factory=list)
    sorting: List[str] = Field(default_factory=list)
    limit: Optional[int] = Field(None)
    date_boundaries: Dict[str, Any] = Field(default_factory=dict)
    business_rules: List[str] = Field(default_factory=list)
    rag_evidence: str = Field("", description="RAG retrieved schema and history context to ground the LLM.")
    missing_information: List[str] = Field(default_factory=list)
