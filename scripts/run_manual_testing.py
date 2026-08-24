"""
Interactive Manual Testing CLI Sandbox for JGH AI Collaborator.
Keeps running in a terminal loop allowing real-time testing of prompts,
displaying intent classification, RAG context, generated SQL, gatekeeper validation flags,
and synthesized ChatGPT-style responses.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

from app.agent.intent_router import route_intent
from app.agent.collaborator import handle_collaborative_query
from app.agent.knowledge_chat import knowledge_chat_agent
from app.validator.query_validator import query_validator

def start_interactive_sandbox():
    print("=" * 75)
    print(" 🤖 JGH AI Collaborator — Interactive Manual Testing Sandbox")
    print(" Type your prompt below to test live intent routing, RAG context & SQL generation.")
    print(" Type 'exit' or 'quit' to close sandbox.")
    print("=" * 75 + "\n")

    while True:
        try:
            user_input = input("\n💬 Type your prompt: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting sandbox. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("Exiting sandbox. Goodbye!")
            break

        print("\n" + "-" * 70)
        print(f"🔍 Analyzing Prompt: \"{user_input}\"")

        # 1. Intent Router
        intent = route_intent(user_input)
        print(f"🎯 Classified Intent: {intent}")

        # 2. RAG Context Lookup for conceptual prompts
        if intent == "TUTOR_QA":
            concept_res = knowledge_chat_agent.answer_conceptual_question(user_input)
            ctx = concept_res.get("retrieved_context", [])
            if ctx:
                print(f"📚 RAG Context Injected:\n{ctx[0][:300]}...")

        # 3. Process Query
        result = handle_collaborative_query(user_input, execute=True)

        sql = result.get("generated_sql", "")
        if sql:
            print(f"\n💻 Generated SQL Query:\n{sql}")

            # Gatekeeper Validation
            ast_val = query_validator.validate_ast(sql)
            plan_val = query_validator.validate_execution_plan(sql)
            print(f"🛡️ Gatekeeper Checks: AST={ast_val['status']} | EXPLAIN={plan_val['status']}")

        # 4. Synthesized Response
        response_text = result.get("response", "")
        print(f"\n🤖 AI Response Output:\n{response_text}")

        follow_ups = result.get("meta", {}).get("follow_ups", [])
        if follow_ups:
            print("\n💡 Suggested Follow-Ups:")
            for f in follow_ups:
                print(f"   • {f}")

        print("-" * 70)

if __name__ == "__main__":
    start_interactive_sandbox()
