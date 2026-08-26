from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BusinessRequirement(BaseModel):
    """
    Canonical representation of a user's natural language business request.
    Generated purely by the LLM NLP Understanding phase.
    """
    original_question: str = Field(..., description="The exact original user question without modification.")
    intent: str = Field(..., description="A short classification of the business intent (e.g. comparative_analytics, list_entities, aggregate_analytics, profile_lookup).")
    entities: List[str] = Field(default_factory=list, description="List of primary entities involved (e.g., retailer, distributor, wallet_transaction).")
    entity_roles: Dict[str, str] = Field(default_factory=dict, description="Specific roles for entities if applicable.")
    relationships: List[str] = Field(default_factory=list, description="Description of relationships required (e.g., 'retailer linked to distributor').")
    specific_ids: Dict[str, Any] = Field(default_factory=dict, description="Any specific identifiers extracted (e.g., {'distributor_id': 5997}).")
    metrics: List[str] = Field(default_factory=list, description="Metrics requested (e.g., 'earnings', 'count').")
    aggregation: List[str] = Field(default_factory=list, description="Aggregation functions required (e.g., 'SUM', 'COUNT').")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="Explicit filters requested (e.g., [{'column': 'status', 'operator': '=', 'value': 'approved'}]).")
    date_period: Optional[str] = Field(None, description="The specific date or time period mentioned (e.g., 'current month', 'last 30 days').")
    relative_dates: Optional[str] = Field(None, description="Relative dates like 'current month' or 'last month'.")
    comparisons: List[str] = Field(default_factory=list, description="Any comparative requirements (e.g., 'vs last month').")
    grouping: List[str] = Field(default_factory=list, description="How the results should be grouped (e.g., 'individual retailer', 'by state').")
    sorting: List[str] = Field(default_factory=list, description="How results should be ordered (e.g., 'highest earnings first').")
    ranking: Optional[str] = Field(None, description="Ranking requirement (e.g., 'top 5').")
    limit: Optional[int] = Field(None, description="Row limit if explicitly requested or implied by ranking.")
    requested_columns: List[str] = Field(default_factory=list, description="The specific columns the user wants in the output.")
    output_format: str = Field("summary", description="Requested output format ('table', 'summary', 'comparison').")
    conditions: List[str] = Field(default_factory=list, description="Any other specific conditions or constraints.")
    clarification_required: bool = Field(False, description="Set to true if the question is dangerously ambiguous and requires user clarification before proceeding.")
    clarification_reason: Optional[str] = Field(None, description="Reason why clarification is needed.")
    context_requirements: Dict[str, Any] = Field(default_factory=dict, description="Inherited or follow-up context.")
