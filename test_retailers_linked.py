from app.agent.sql_agent import run_agent
import json

res = run_agent("Generate a table of retailers linked to distributor 5997")
print(json.dumps(res, indent=2))
