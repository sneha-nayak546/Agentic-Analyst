import sys
import os
sys.path.insert(0, os.path.abspath("."))

from app.prompt.prompt_builder import build_sql_prompt
from app.knowledge.relationship_resolver import relationship_resolver
from app.agent.nlp_understanding import nlp_agent

req = nlp_agent.parse_question("Show top 3 retailers by earnings for July 2026")
plan = relationship_resolver.resolve(req)
prompt = build_sql_prompt(plan)
print(f"Total characters: {len(prompt)}")
print(f"Estimated tokens: {len(prompt) // 4}")
print("\n" + prompt[:400] + "\n...\n" + prompt[-400:])
