from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AtomicTask(BaseModel):
    """
    Sub-task representation for multi-part or comparative requests.
    """
    task_id: int = Field(1, description="Sequential task identifier.")
    description: str = Field(..., description="Self-contained description of the atomic task.")
    intent: str = Field(..., description="Intent of this specific atomic task.")
    entities: List[str] = Field(default_factory=list, description="Target entities for this task.")
    metrics: List[str] = Field(default_factory=list, description="Metrics to compute.")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="Filters specific to this task.")
    date_period: Optional[str] = Field(None, description="Date filter for this task.")
    grouping: List[str] = Field(default_factory=list, description="Grouping dimensions.")
    sorting: List[str] = Field(default_factory=list, description="Sort order.")
    limit: Optional[int] = Field(None, description="Row limit.")

class BusinessRequirement(BaseModel):
    """
    Canonical structured representation of a user's natural language business request.
    Enforces the strict Business Requirement Contract.
    """
    original_question: str = Field(..., description="The exact original user question without modification.")
    intent: str = Field(..., description="A short classification of the business intent.")
    query_type: str = Field("data_retrieval", description="High level query type: 'scalar', 'list', 'ranking', 'timeseries', 'comparison', 'multi_part'.")
    entities: List[str] = Field(default_factory=list, description="Target entities mentioned (e.g., retailer, distributor, wallet_transaction).")
    entity_roles: Dict[str, str] = Field(default_factory=dict, description="Specific roles for entities if applicable.")
    relationships: List[str] = Field(default_factory=list, description="Description of relationships required.")
    specific_ids: Dict[str, Any] = Field(default_factory=dict, description="Any specific identifiers extracted.")
    metric: Optional[str] = Field(None, description="Primary normalized metric concept.")
    metrics: List[str] = Field(default_factory=list, description="Metrics requested (e.g., 'earnings', 'count', 'wallet_balance', 'total wallet transactions').")
    metric_source: Optional[str] = Field(None, description="Verified table.column source of metric (e.g. sku_inventories.id).")
    aggregation: List[str] = Field(default_factory=list, description="Aggregation functions required (e.g., 'SUM', 'COUNT', 'AVG').")
    dimensions: List[str] = Field(default_factory=list, description="Requested breakdown dimensions.")
    dimension_sources: Dict[str, str] = Field(default_factory=dict, description="Verified physical sources of dimensions (e.g. {'distributor': 'users.id'}).")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="Explicit filters requested.")
    dates: List[str] = Field(default_factory=list, description="Explicit dates mentioned.")
    periods: List[str] = Field(default_factory=list, description="Explicit periods mentioned (e.g., 'July 2026', 'June 2026').")
    date_period: Optional[str] = Field(None, description="The primary date or time period mentioned.")
    time_column: Optional[str] = Field(None, description="Verified physical timestamp column (e.g. sku_inventories.retailer_scanned_at).")
    time_range: Optional[Dict[str, Any]] = Field(None, description="Dynamic runtime time boundaries.")
    relative_dates: Optional[str] = Field(None, description="Relative dates like 'current month' or 'last month'.")
    comparison: Optional[Any] = Field(None, description="Comparison requirement or specs.")
    comparisons: List[str] = Field(default_factory=list, description="Any comparative requirements.")
    comparison_specs: Dict[str, Any] = Field(default_factory=dict, description="Structured comparison spec.")
    grouping: List[str] = Field(default_factory=list, description="How results should be grouped.")
    sorting: List[str] = Field(default_factory=list, description="How results should be ordered.")
    ranking: Optional[str] = Field(None, description="Ranking requirement (e.g., 'top 10').")
    ranking_direction: Optional[str] = Field(None, description="Sort direction for ranking: DESC or ASC.")
    ranking_limit: Optional[int] = Field(None, description="Explicit row limit for ranking.")
    limit: Optional[int] = Field(None, description="Row limit if explicitly requested or implied by ranking.")
    relationship_path: List[str] = Field(default_factory=list, description="Verified join paths connecting dimensions and metrics.")
    requested_columns: List[str] = Field(default_factory=list, description="The specific columns the user wants in the output.")
    output_type: str = Field("summary", description="Requested output format: 'table', 'summary', 'scalar', 'comparison'.")
    output_format: str = Field("summary", description="Backward-compatible alias for output_type.")
    conditions: List[str] = Field(default_factory=list, description="Any other specific conditions or constraints.")
    clarification_required: bool = Field(False, description="Set to true if the question is dangerously ambiguous.")
    clarification_reason: Optional[str] = Field(None, description="Reason why clarification is needed.")
    atomic_tasks: List[AtomicTask] = Field(default_factory=list, description="Sub-tasks if request is multi-part or comparative.")
    context_classification: str = Field("NEW_QUERY", description="Context classification.")
    confidence: float = Field(1.0, description="Confidence score of understanding (0.0 to 1.0).")
    context_requirements: Dict[str, Any] = Field(default_factory=dict, description="Inherited or follow-up context.")

    def to_structured_intent(self) -> Dict[str, Any]:
        """Returns the strict structured intent dictionary per Section 3."""
        import re
        p_raw = self.date_period or (self.periods[0] if self.periods else "")
        month = None
        year = None
        p_lower = p_raw.lower()
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }
        for m_name, m_num in month_map.items():
            if m_name in p_lower:
                month = m_num
                break

        y_match = re.search(r"\b(202\d)\b", p_raw)
        if y_match:
            year = int(y_match.group(1))

        start_date = None
        end_date = None
        if month and year:
            start_date = f"{year:04d}-{month:02d}-01"
            end_date = f"{year:04d}-{month+1:02d}-01" if month < 12 else f"{year+1:04d}-01-01"
        elif year:
            start_date = f"{year:04d}-01-01"
            end_date = f"{year+1:04d}-01-01"

        time_period_obj = {
            "start": start_date,
            "end": end_date,
            "type": "month" if month else ("year" if year else ("period" if p_raw else "all_time")),
            "month": month,
            "year": year,
            "raw": p_raw
        }

        sort_val = self.ranking_direction or (
            "DESC" if (self.ranking or self.intent == "ranking" or (self.sorting and any("desc" in s.lower() for s in self.sorting))) else (
                "ASC" if (self.sorting and any("asc" in s.lower() for s in self.sorting)) else "NONE"
            )
        )

        return {
            "intent_type": self.intent or "data_retrieval",
            "entities": self.entities,
            "entity": self.entities[0] if self.entities else None,
            "metric": self.metric or (self.metrics[0] if self.metrics else None),
            "metric_source": self.metric_source,
            "aggregation": self.aggregation[0].upper() if self.aggregation else "SUM",
            "dimensions": self.dimensions or [],
            "dimension_sources": self.dimension_sources,
            "time_column": self.time_column,
            "time_range": self.time_range or time_period_obj,
            "period": time_period_obj,
            "time_period": time_period_obj,
            "ranking_direction": sort_val,
            "ranking_limit": self.ranking_limit or self.limit,
            "limit": self.limit,
            "sort": sort_val,
            "relationship_path": self.relationship_path,
            "filters": self.filters
        }



