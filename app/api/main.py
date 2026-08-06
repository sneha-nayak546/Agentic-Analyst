from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.agent.sql_agent import run_agent
from app.database.read_executor import execute_read_query
from app.utils.report_generator import generate_csv, generate_excel, generate_pdf, generate_csv_stream, save_reports_to_disk
from app.sql_history.query_history import log_query_history, get_query_history
from app.utils.summary_generator import generate_natural_summary

import sys
import json
import os
import uuid
import subprocess
from contextlib import asynccontextmanager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# Ensure reports directory exists
os.makedirs("reports", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.knowledge.db_profiler import run_database_profiler
        from app.knowledge.knowledge_graph import get_knowledge_graph

        schema_file = "knowledge/schema/schema_metadata.json"
        if not os.path.exists(schema_file):
            from app.database.metadata_extractor import generate_enterprise_knowledge_base
            print("[STARTUP] Extracting complete enterprise database schema metadata...")
            generate_enterprise_knowledge_base()

        print("[STARTUP] Pre-loading Knowledge Graph...")
        run_database_profiler()
        get_knowledge_graph()
    except Exception as e:
        print("[STARTUP NOTICE]", e)
    print("[STARTUP COMPLETE] Enterprise AI SQL Agent ready on http://localhost:8000")
    yield


app = FastAPI(
    title="AI SQL Agent Intelligence Platform",
    description="Production Read-Only AI SQL Agent for Enterprise Reporting",
    version="2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")


class QueryRequest(BaseModel):
    question: str
    execute: Optional[bool] = True


class ExportRequest(BaseModel):
    columns: List[str]
    data: List[Dict]
    filename: Optional[str] = "report"


class SqlExportRequest(BaseModel):
    sql: str
    filename: Optional[str] = "query_export"


class SettingsRequest(BaseModel):
    model_name: Optional[str] = "qwen2.5-coder:7b"
    embedding_model: Optional[str] = "all-MiniLM-L6-v2"
    temperature: Optional[float] = 0.1
    top_k: Optional[int] = 4
    max_rows: Optional[int] = 100


APP_SETTINGS = {
    "model_name": "qwen2.5-coder:7b",
    "embedding_model": "all-MiniLM-L6-v2",
    "temperature": 0.1,
    "top_k": 4,
    "max_rows": 100
}


def _get_schema_map() -> dict:
    """Returns a clean map of {table_name: [col1, col2, ...]} from schema metadata."""
    schema_file = "knowledge/schema/schema_metadata.json"
    schema_map = {}
    if os.path.exists(schema_file):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for tbl, info in raw.items():
                cols = list(info.get("columns", {}).keys())
                schema_map[tbl] = cols
        except Exception:
            pass
    return schema_map


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
def health_check():
    db_check = execute_read_query("SELECT 1 AS status;", limit=1)
    
    schema_file = "knowledge/schema/schema_metadata.json"
    table_count = 0
    if os.path.exists(schema_file):
        with open(schema_file, "r") as f:
            table_count = len(json.load(f))
            
    return {
        "status": "online" if db_check["success"] else "database_error",
        "database_connected": db_check["success"],
        "target_tables_count": table_count,
        "llm_model": APP_SETTINGS["model_name"]
    }


@app.get("/schema")
def get_schema():
    """Returns a clean {table: [columns]} map for the frontend schema panel."""
    return {"schema": _get_schema_map()}


from fastapi.responses import StreamingResponse

@app.post("/query")
def query_database(request: QueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = run_agent(request.question, "", execute=request.execute)

        # --- Root cause fix: map internal result keys to standardized response ---
        exec_res = result.get("execution", {})
        columns = exec_res.get("columns", [])
        rows = exec_res.get("data", [])
        exec_success = exec_res.get("success", False)
        exec_time_ms = exec_res.get("execution_time_ms", 0)
        row_count = exec_res.get("row_count", len(rows))
        sql_query = result.get("optimized_sql") or result.get("generated_sql", "")
        status = result.get("status", "unknown")

        # Handle blocked/ambiguous cases
        if result.get("is_ambiguous"):
            return {
                "status": "ambiguous",
                "question": result.get("question", request.question),
                "sql_query": "",
                "execution_time": 0,
                "rows_returned": 0,
                "summary": result.get("clarification", "Ambiguous query."),
                "results": [],
                "report_urls": {},
                "schema": _get_schema_map(),
                "clarification": result.get("clarification"),
                "options": result.get("options", []),
            }

        if status == "blocked" or not exec_success:
            error_msg = exec_res.get("error") or result.get("validation", {}).get("reason", "Query failed.")
            if not result.get("is_ambiguous"):
                log_query_history(
                    question=request.question,
                    generated_sql=result.get("generated_sql", ""),
                    optimized_sql=sql_query,
                    status="error",
                    execution_time_ms=exec_time_ms,
                    row_count=0,
                    affected_tables=result.get("affected_tables", []),
                    error=error_msg,
                )
            return {
                "status": "error",
                "message": error_msg,
                "question": result.get("question", request.question),
                "sql_query": sql_query,
                "execution_time": exec_time_ms,
                "rows_returned": 0,
                "summary": "",
                "results": [],
                "report_urls": {},
                "schema": _get_schema_map(),
            }

        # Generate reports
        report_id = str(uuid.uuid4())[:8]
        report_urls = {}
        try:
            report_urls = save_reports_to_disk(columns, rows, report_id)
        except Exception as e:
            print(f"[REPORT WARNING] Could not generate reports: {e}")

        # Generate natural language summary
        summary = generate_natural_summary(request.question, sql_query, columns, rows)

        # Log history
        if not result.get("is_ambiguous"):
            log_query_history(
                question=request.question,
                generated_sql=result.get("generated_sql", ""),
                optimized_sql=sql_query,
                status=status,
                execution_time_ms=exec_time_ms,
                row_count=row_count,
                affected_tables=result.get("affected_tables", []),
                error=exec_res.get("error"),
                confidence_score=result.get("confidence_score"),
                execution_plan=result.get("execution_plan"),
                explanation=result.get("explanation"),
                thinking_steps=result.get("thinking_steps"),
            )

        return {
            "status": "success",
            "question": result.get("question", request.question),
            "sql_query": sql_query,
            "execution_time": exec_time_ms,
            "rows_returned": row_count,
            "summary": summary,
            "results": rows,
            "columns": columns,
            "report_urls": report_urls,
            "schema": _get_schema_map(),
            # Legacy fields kept for history/admin tabs
            "generated_sql": result.get("generated_sql", ""),
            "optimized_sql": sql_query,
            "explanation": result.get("explanation", ""),
            "confidence_score": result.get("confidence_score"),
            "thinking_steps": result.get("thinking_steps", []),
            "affected_tables": result.get("affected_tables", []),
            "reasoning": result.get("reasoning", {}),
            "execution": exec_res,
            "benchmarks": result.get("benchmarks", {}),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "question": request.question,
            "sql_query": "",
            "execution_time": 0,
            "rows_returned": 0,
            "summary": "",
            "results": [],
            "report_urls": {},
            "schema": _get_schema_map(),
        }


@app.post("/query/stream")
async def query_database_stream(request: QueryRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    async def event_generator():
        yield f"data: {json.dumps({'status': 'step', 'message': 'Detecting intent...'})}\\n\\n"
        yield f"data: {json.dumps({'status': 'step', 'message': 'Finding schema...'})}\\n\\n"
        yield f"data: {json.dumps({'status': 'step', 'message': 'Generating SQL...'})}\\n\\n"
        
        try:
            result = run_agent(request.question, "", execute=request.execute)

            yield f"data: {json.dumps({'status': 'step', 'message': 'Validating SQL...'})}\\n\\n"
            yield f"data: {json.dumps({'status': 'step', 'message': 'Executing query...'})}\\n\\n"
            yield f"data: {json.dumps({'status': 'complete', 'message': 'Preparing report...', 'result': result})}\\n\\n"

            if not result.get("is_ambiguous"):
                exec_res = result.get("execution", {})
                log_query_history(
                    question=request.question,
                    generated_sql=result.get("generated_sql", ""),
                    optimized_sql=result.get("optimized_sql", ""),
                    status=result.get("status", "unknown"),
                    execution_time_ms=exec_res.get("execution_time_ms", 0),
                    row_count=exec_res.get("row_count", 0),
                    affected_tables=result.get("affected_tables", []),
                    error=exec_res.get("error")
                )
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/export/csv")
def export_csv(req: ExportRequest):
    filename = f"{req.filename}.csv"
    return StreamingResponse(
        generate_csv_stream(req.columns, req.data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/export/json")
def export_json(req: ExportRequest):
    filename = f"{req.filename}.json"
    content = json.dumps(req.data, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/export/excel")
def export_excel(req: ExportRequest):
    content = generate_excel(req.columns, req.data)
    filename = f"{req.filename}.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/export/pdf")
def export_pdf(req: ExportRequest):
    content = generate_pdf(req.columns, req.data)
    filename = f"{req.filename}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/export/sql")
def export_sql(req: SqlExportRequest):
    filename = f"{req.filename}.sql"
    return Response(
        content=req.sql.encode("utf-8"),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/history")
def fetch_history(limit: int = 100, search: Optional[str] = None):
    return {"history": get_query_history(limit=limit, search=search)}


class HistoryActionRequest(BaseModel):
    timestamp: str

@app.post("/history/favorite")
def favorite_history(req: HistoryActionRequest):
    from app.sql_history.query_history import toggle_favorite_history
    success = toggle_favorite_history(req.timestamp)
    return {"success": success}

@app.post("/history/delete")
def delete_history(req: HistoryActionRequest):
    from app.sql_history.query_history import delete_history_item
    success = delete_history_item(req.timestamp)
    return {"success": success}


@app.get("/admin/tables")
def get_admin_tables():
    schema_file = "knowledge/schema/schema_metadata.json"
    table_info = []
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
            for tbl, info in schema.items():
                table_info.append({
                    "table_name": tbl,
                    "status": "active_in_scope",
                    "row_count": info.get("row_count", "N/A")
                })
    return {"tables": table_info}


@app.get("/admin/schema")
def get_admin_schema():
    schema_file = "knowledge/schema/schema_metadata.json"
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            return {"schema": json.load(f)}
    return {"schema": {}}


@app.get("/admin/knowledge-graph")
def get_admin_knowledge_graph():
    from app.knowledge.knowledge_graph import get_knowledge_graph
    kg = get_knowledge_graph()
    return {
        "nodes": list(kg.nodes.values()),
        "edges": kg.edges,
        "metadata": kg.business_meta
    }


@app.get("/admin/status")
def get_admin_status():
    db_check = execute_read_query("SELECT 1 AS status;", limit=1)
    history = get_query_history(limit=500)
    
    schema_file = "knowledge/schema/schema_metadata.json"
    target_tables = []
    if os.path.exists(schema_file):
        with open(schema_file, "r") as f:
            target_tables = list(json.load(f).keys())
            
    return {
        "database_connected": db_check["success"],
        "target_tables_count": len(target_tables),
        "target_tables": sorted(target_tables),
        "embedding_status": f"ChromaDB Ready ({APP_SETTINGS['embedding_model']})",
        "rag_collections": ["enterprise_schema"],
        "sql_history_count": len(history),
        "model_status": f"Ollama / {APP_SETTINGS['model_name']} (Local & Offline)"
    }


@app.post("/admin/rebuild-embeddings")
def rebuild_embeddings():
    try:
        from app.embedding.chroma_builder import build_embeddings
        res = build_embeddings(model_name=APP_SETTINGS["embedding_model"])
        return {"status": "success", "message": "Vector store embeddings rebuilt successfully.", "details": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/admin/refresh-metadata")
def refresh_metadata():
    try:
        from app.database.metadata_extractor import generate_enterprise_knowledge_base
        generate_enterprise_knowledge_base()
        return {"status": "success", "message": "Database schema metadata refreshed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/admin/settings")
def get_settings():
    return APP_SETTINGS


@app.post("/admin/settings")
def update_settings(req: SettingsRequest):
    if req.model_name:
        APP_SETTINGS["model_name"] = req.model_name
    if req.embedding_model:
        APP_SETTINGS["embedding_model"] = req.embedding_model
    if req.temperature is not None:
        APP_SETTINGS["temperature"] = req.temperature
    if req.top_k is not None:
        APP_SETTINGS["top_k"] = req.top_k
    if req.max_rows is not None:
        APP_SETTINGS["max_rows"] = req.max_rows
    return {"status": "success", "settings": APP_SETTINGS}


@app.get("/admin/stats")
def get_admin_stats():
    stats = {
        "tables_tracked": 0,
        "relationships_mapped": 0,
        "vocab_size": 0,
        "query_history_count": 0,
        "avg_latency_ms": 0.0,
        "avg_confidence": 0.0
    }
    
    try:
        schema_file = "knowledge/schema/schema_metadata.json"
        if os.path.exists(schema_file):
            with open(schema_file, "r", encoding="utf-8") as f:
                stats["tables_tracked"] = len(json.load(f))
                
        rel_file = "knowledge/graph/relationship_metadata.json"
        if os.path.exists(rel_file):
            with open(rel_file, "r", encoding="utf-8") as f:
                stats["relationships_mapped"] = len(json.load(f))
                
        vocab_file = "knowledge/business_metadata.json"
        if os.path.exists(vocab_file):
            with open(vocab_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                stats["vocab_size"] = len(data.get("business_terminology", {}))
                
        history = get_query_history(limit=1000)
        stats["query_history_count"] = len(history)
        
        if history:
            total_latency = sum([h.get("execution_time_ms", 0) or 0 for h in history])
            stats["avg_latency_ms"] = round(total_latency / len(history), 2)
            
            total_conf = sum([h.get("confidence_score", 100) or 100 for h in history])
            stats["avg_confidence"] = round(total_conf / len(history), 2)
            
    except Exception as e:
        print("Stats error:", e)
        
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)