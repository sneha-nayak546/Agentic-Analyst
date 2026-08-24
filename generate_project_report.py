from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors

content = [
    ('Project Handbook', 'Heading1'),
    ('Overview', 'Heading2'),
    ('This repository implements an enterprise AI SQL agent platform with a Python backend API, a React frontend, schema-aware SQL generation, MySQL read-only execution, query history, and report export.', 'BodyText'),
    ('Architecture', 'Heading2'),
    ('User request flow:', 'BodyText'),
    ('1. Browser frontend sends a natural-language question.', 'BodyText'),
    ('2. FastAPI backend receives /query and routes to the AI SQL agent.', 'BodyText'),
    ('3. SQL generation uses the knowledge graph, query planner, prompt builder, and Ollama local model.', 'BodyText'),
    ('4. Validated SQL is executed against MySQL and results are returned.', 'BodyText'),
    ('Component Breakdown', 'Heading2'),
    ('Backend', 'Heading3'),
    ('- app/api/main.py: FastAPI application and endpoints.', 'BodyText'),
    ('- app/agent/sql_agent.py: Orchestration pipeline.', 'BodyText'),
    ('- app/agent/query_planner.py: Builds deterministic execution plans.', 'BodyText'),
    ('- app/agent/ambiguity_checker.py: Detects ambiguous user questions.', 'BodyText'),
    ('- app/llm/sql_generator.py: Generates SQL via Ollama or fallback logic.', 'BodyText'),
    ('- app/prompt/prompt_builder.py: Builds strict prompts with table/column context.', 'BodyText'),
    ('- app/database/read_executor.py: Executes read-only MySQL queries.', 'BodyText'),
    ('- app/knowledge/knowledge_graph.py: Loads schema and relationship metadata.', 'BodyText'),
    ('- app/utils/report_generator.py: Exports CSV, Excel, and PDF reports.', 'BodyText'),
    ('- app/sql_history/query_history.py: Logs query history and audits.', 'BodyText'),
    ('Frontend', 'Heading3'),
    ('- React + Vite app in frontend/src to provide query, history, admin, and settings UI.', 'BodyText'),
    ('Tech Stack', 'Heading2'),
    ('- Python, FastAPI, Uvicorn, SQLAlchemy, PyMySQL, pandas, reportlab.', 'BodyText'),
    ('- React, Vite, lucide-react, recharts.', 'BodyText'),
    ('- Ollama local model for offline SQL generation.', 'BodyText'),
    ('- MySQL read-only database backend.', 'BodyText'),
    ('Why this design', 'Heading2'),
    ('- FastAPI for fast API development and static file hosting.', 'BodyText'),
    ('- React + Vite for responsive frontend and rapid development.', 'BodyText'),
    ('- Knowledge graph and deterministic prompt structure to reduce hallucinations.', 'BodyText'),
    ('- Ollama local model to keep inference offline and self-contained.', 'BodyText'),
    ('- SQL validation and EXPLAIN checks for safer query execution.', 'BodyText'),
    ('Setup & Run', 'Heading2'),
    ('1. Create a Python virtual environment and install requirements.', 'BodyText'),
    ('2. Add database credentials to .env: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD.', 'BodyText'),
    ('3. Start backend: python app/main.py or python -m uvicorn app.api.main:app --reload.', 'BodyText'),
    ('4. Start frontend: cd frontend && npm install && npm run dev.', 'BodyText'),
    ('Useful Endpoints', 'Heading2'),
    ('- POST /query', 'BodyText'),
    ('- POST /query/stream', 'BodyText'),
    ('- GET /history', 'BodyText'),
    ('- GET /admin/status, /admin/schema, /admin/tables, /admin/knowledge-graph', 'BodyText'),
    ('- POST /admin/rebuild-embeddings, /admin/refresh-metadata', 'BodyText'),
    ('- POST /export/csv, /export/excel, /export/pdf, /export/json, /export/sql', 'BodyText'),
    ('Key Files', 'Heading2'),
    ('- requirements.txt, frontend/package.json', 'BodyText'),
    ('- app/api/main.py, app/agent/sql_agent.py, app/llm/sql_generator.py, app/database/read_executor.py.', 'BodyText'),
    ('Notes', 'Heading2'),
    ('- The system is designed for read-only analytics and safe SQL generation.', 'BodyText'),
    ('- Ollama should run locally at http://127.0.0.1:11434 for LLM mode.', 'BodyText'),
    ('- Generated reports are saved under reports/ and exposed via /reports/<id>.', 'BodyText'),
    ('Quick Start Commands', 'Heading2'),
    ('python -m venv .venv', 'BodyText'),
    ('.venv\\Scripts\\Activate.ps1', 'BodyText'),
    ('pip install -r requirements.txt', 'BodyText'),
    ('python app/main.py', 'BodyText'),
    ('cd frontend && npm install && npm run dev', 'BodyText'),
]

pdf_path = 'PROJECT_REPORT.pdf'

doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
styles = getSampleStyleSheet()
styles['Heading1'].fontSize = 20
styles['Heading1'].leading = 24
styles['Heading1'].spaceAfter = 14
styles['Heading1'].textColor = colors.HexColor('#1d4ed8')
styles['Heading2'].fontSize = 16
styles['Heading2'].leading = 20
styles['Heading2'].spaceBefore = 12
styles['Heading2'].spaceAfter = 8
styles['Heading2'].textColor = colors.HexColor('#0f172a')
styles['Heading3'].fontSize = 14
styles['Heading3'].leading = 18
styles['Heading3'].spaceBefore = 10
styles['Heading3'].spaceAfter = 6
styles['Heading3'].textColor = colors.HexColor('#111827')
styles['BodyText'].fontSize = 11
styles['BodyText'].leading = 14
styles['BodyText'].spaceAfter = 4

flow = []
for text, style in content:
    flow.append(Paragraph(text, styles[style]))
    flow.append(Spacer(1, 4))

doc.build(flow)
print(f'PDF generated: {pdf_path}')
