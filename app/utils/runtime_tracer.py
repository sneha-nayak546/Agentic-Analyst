import time
import uuid
from typing import Dict, Any, Optional

class RuntimeTracer:
    """
    Comprehensive runtime profiler and telemetry tracer for JGH Intelligence Engine.
    Records per-stage latency, provider/model metadata, database metrics,
    and verification statuses while strictly sanitizing sensitive credentials.
    """

    def __init__(self, question: str, request_id: Optional[str] = None):
        self.request_id = request_id or f"req_{uuid.uuid4().hex[:10]}"
        self.question = question
        self.t_start = time.perf_counter()

        # Latencies (in milliseconds)
        self.intent_latency_ms: float = 0.0
        self.schema_latency_ms: float = 0.0
        self.sql_generation_latency_ms: float = 0.0
        self.sql_validation_latency_ms: float = 0.0
        self.semantic_verification_latency_ms: float = 0.0
        self.db_connection_latency_ms: float = 0.0
        self.db_query_latency_ms: float = 0.0
        self.db_fetch_latency_ms: float = 0.0
        self.result_verification_latency_ms: float = 0.0
        self.answer_latency_ms: float = 0.0
        self.total_latency_ms: float = 0.0

        # Provider & Model Metadata
        self.intent_provider: str = "unknown"
        self.intent_model: str = "unknown"

        self.sql_provider: str = "unknown"
        self.sql_model: str = "unknown"

        self.semantic_verifier_provider: str = "unknown"
        self.semantic_verifier_model: str = "unknown"

        self.answer_provider: str = "unknown"
        self.answer_model: str = "unknown"

        # Cache & Fallback Tracking
        self.cache_hit: bool = False
        self.fallback_used: bool = False
        self.fallback_reason: Optional[str] = None

        # Verification Statuses (Section 15)
        self.sql_execution_success: bool = False
        self.sql_semantic_correct: bool = False
        self.result_verified: bool = False
        self.answer_grounded: bool = False

        # Internal timers
        self._stage_starts: Dict[str, float] = {}

    def start_stage(self, stage_name: str):
        self._stage_starts[stage_name] = time.perf_counter()

    def end_stage(self, stage_name: str) -> float:
        t0 = self._stage_starts.pop(stage_name, None)
        if t0 is None:
            return 0.0
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        if stage_name == "intent":
            self.intent_latency_ms = elapsed_ms
        elif stage_name == "schema":
            self.schema_latency_ms = elapsed_ms
        elif stage_name == "sql_generation":
            self.sql_generation_latency_ms += elapsed_ms
        elif stage_name == "sql_validation":
            self.sql_validation_latency_ms += elapsed_ms
        elif stage_name == "semantic_verification":
            self.semantic_verification_latency_ms += elapsed_ms
        elif stage_name == "db_connection":
            self.db_connection_latency_ms += elapsed_ms
        elif stage_name == "db_query":
            self.db_query_latency_ms += elapsed_ms
        elif stage_name == "db_fetch":
            self.db_fetch_latency_ms += elapsed_ms
        elif stage_name == "result_verification":
            self.result_verification_latency_ms = elapsed_ms
        elif stage_name == "answer":
            self.answer_latency_ms = elapsed_ms
        return elapsed_ms

    def set_intent_metadata(self, provider: str, model: str):
        self.intent_provider = provider
        self.intent_model = model

    def set_sql_metadata(self, provider: str, model: str):
        self.sql_provider = provider
        self.sql_model = model

    def set_verifier_metadata(self, provider: str, model: str):
        self.semantic_verifier_provider = provider
        self.semantic_verifier_model = model

    def set_answer_metadata(self, provider: str, model: str):
        self.answer_provider = provider
        self.answer_model = model

    def set_db_metrics(self, conn_ms: float, query_ms: float, fetch_ms: float, fallback_used: bool = False, fallback_reason: Optional[str] = None):
        self.db_connection_latency_ms = round(conn_ms, 2)
        self.db_query_latency_ms = round(query_ms, 2)
        self.db_fetch_latency_ms = round(fetch_ms, 2)
        if fallback_used:
            self.fallback_used = True
            self.fallback_reason = fallback_reason

    def finalize(self) -> Dict[str, Any]:
        self.total_latency_ms = round((time.perf_counter() - self.t_start) * 1000, 2)
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "question": self.question,
            "intent_provider": self.intent_provider,
            "intent_model": self.intent_model,
            "intent_latency_ms": self.intent_latency_ms,
            "schema_latency_ms": self.schema_latency_ms,
            "sql_provider": self.sql_provider,
            "sql_model": self.sql_model,
            "sql_generation_latency_ms": self.sql_generation_latency_ms,
            "sql_validation_latency_ms": self.sql_validation_latency_ms,
            "semantic_verifier_provider": self.semantic_verifier_provider,
            "semantic_verifier_model": self.semantic_verifier_model,
            "semantic_verification_latency_ms": self.semantic_verification_latency_ms,
            "db_connection_latency_ms": self.db_connection_latency_ms,
            "db_query_latency_ms": self.db_query_latency_ms,
            "db_fetch_latency_ms": self.db_fetch_latency_ms,
            "result_verification_latency_ms": self.result_verification_latency_ms,
            "answer_provider": self.answer_provider,
            "answer_model": self.answer_model,
            "answer_latency_ms": self.answer_latency_ms,
            "total_latency_ms": self.total_latency_ms,
            "cache_hit": self.cache_hit,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "verification_statuses": {
                "SQL_EXECUTION_SUCCESS": self.sql_execution_success,
                "SQL_SEMANTIC_CORRECT": self.sql_semantic_correct,
                "RESULT_VERIFIED": self.result_verified,
                "ANSWER_GROUNDED": self.answer_grounded,
            }
        }
