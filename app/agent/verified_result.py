"""
Canonical VerifiedResult module for JGH Intelligence Engine.
Acts as the SINGLE SOURCE OF TRUTH for all downstream presentation:
UI DataGrid, API responses, natural language answer, and CSV/Excel/PDF exports.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Status Constants
VERIFIED = "VERIFIED"
VERIFIED_PARTIAL = "VERIFIED_PARTIAL"
VERIFIED_EMPTY = "VERIFIED_EMPTY"
INVALID = "INVALID"
SUSPICIOUS_RESULT = "SUSPICIOUS_RESULT"
BLOCKED = "BLOCKED"
ERROR = "ERROR"
UNABLE_TO_VERIFY = "UNABLE_TO_VERIFY"
GROUNDING_INSUFFICIENT = "GROUNDING_INSUFFICIENT"

class VerifiedResult(BaseModel):
    """
    Canonical Verified Result Model.
    Represents WHAT the system executed, verified against the database,
    and checked against the user's BusinessRequirement.
    """
    request_id: str = Field("", description="Unique request identifier.")
    database_identifier: str = Field("mysql://168.144.28.208:3306/jghMasterDB", description="The exact database connection identifier.")
    database_engine: Optional[str] = Field("mysql", description="Underlying DB engine (e.g. mysql, sqlite).")
    database_host: Optional[str] = Field("168.144.28.208", description="Database host IP or hostname.")
    database_port: Optional[str] = Field("3306", description="Database port.")
    database_name: Optional[str] = Field("jghMasterDB", description="Database schema/catalog name.")
    database_source: Optional[str] = Field("CONFIGURED_PRODUCTION_DATABASE", description="Execution source description.")
    timestamp: str = Field("", description="Execution timestamp.")
    question: str = Field(..., description="The original business question asked by the user.")
    business_requirement: Any = Field(..., description="The strict BusinessRequirement contract.")
    execution_plan: Any = Field(..., description="The grounded ExecutionPlan describing query execution.")
    sql: str = Field(..., description="The verified SQL statement executed on the database.")
    columns: List[str] = Field(default_factory=list, description="List of column names returned by MySQL.")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Row records returned by MySQL.")
    row_count: int = Field(0, description="Total number of rows returned.")
    execution_time_ms: float = Field(0.0, description="Database execution time in milliseconds.")
    summary: str = Field("", description="Natural language response grounded strictly on verified data.")
    requirement_diff: str = Field("", description="Rendered [REQUIREMENT DIFF] text block.")
    diff_details: Dict[str, Any] = Field(default_factory=dict, description="Structured diff items and evaluation.")
    validation_status: str = Field(VERIFIED, description="Status: VERIFIED, VERIFIED_PARTIAL, VERIFIED_EMPTY, INVALID, BLOCKED, ERROR.")
    report_urls: Dict[str, str] = Field(default_factory=dict, description="Pre-generated report links (CSV, Excel, PDF).")
    metric: Optional[str] = Field(None, description="The grounded business metric name.")
    dimensions: List[str] = Field(default_factory=list, description="The analytical dimensions returned.")
    periods: List[str] = Field(default_factory=list, description="The time periods included in query or result.")
    ranking: Optional[str] = Field(None, description="Ranking specification (e.g. top 1, bottom 1).")
    null_info: Dict[str, Any] = Field(default_factory=dict, description="Explicit tracking of NULL values vs zeros.")
    error: Optional[str] = Field(None, description="Error message if pipeline execution failed.")
    stage: Optional[str] = Field(None, description="Stage at which failure occurred, if any.")

    @property
    def rows(self) -> List[Dict[str, Any]]:
        """Access rows as a direct property equivalent to data."""
        return self.data

    def to_api_dict(self) -> Dict[str, Any]:
        """Serializes the VerifiedResult for API responses ensuring exact UI + report consistency."""
        req_dict = self.business_requirement.model_dump() if hasattr(self.business_requirement, "model_dump") else self.business_requirement
        plan_dict = self.execution_plan.model_dump() if hasattr(self.execution_plan, "model_dump") else self.execution_plan
        return {
            "request_id": self.request_id,
            "database_identifier": self.database_identifier,
            "database_engine": self.database_engine,
            "database_host": self.database_host,
            "database_port": self.database_port,
            "database_name": self.database_name,
            "database_source": self.database_source,
            "timestamp": self.timestamp,
            "question": self.question,
            "business_requirement": req_dict,
            "execution_plan": plan_dict,
            "sql": self.sql,
            "sql_query": self.sql,
            "columns": self.columns,
            "results": self.data,
            "data": self.data,
            "row_count": self.row_count,
            "rows_returned": self.row_count,
            "execution_time": self.execution_time_ms,
            "summary": self.summary,
            "requirement_diff": self.requirement_diff,
            "diff_details": self.diff_details,
            "validation_status": self.validation_status,
            "result_confidence": self.validation_status,
            "report_urls": self.report_urls,
            "metric": self.metric,
            "dimensions": self.dimensions,
            "periods": self.periods,
            "ranking": self.ranking,
            "null_info": self.null_info,
            "error": self.error,
            "stage": self.stage
        }

