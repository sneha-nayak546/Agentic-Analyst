"""
Multi-Turn Conversation Memory & Context Manager for JGH Intelligence Engine.
Maintains sliding window of turns and structured session context per session_id:
  - Isolated multi-user session state (User A session_id != User B session_id)
  - Seamless context inheritance, replacement, correction, and reset
  - Integrated with ContextResolver
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from app.agent.nlp_intent_parser import nlp_intent_parser

class MemoryManager:
    def __init__(self, max_history_turns: int = 10):
        self.max_turns = max_history_turns
        self.sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.structured_context: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def resolve_session_context(self, session_id: str, current_prompt: str) -> Dict[str, Any]:
        """
        Resolves prompt entities and filters against previous session context.
        Inherits, replaces, or resets context according to natural business logic.
        """
        prev_context = self.structured_context.get(session_id, {}).copy()
        resolved = nlp_intent_parser.parse_intent(current_prompt, previous_context=prev_context)

        if resolved.get("is_reset"):
            self.clear_session(session_id)
            return resolved

        self.structured_context[session_id] = resolved
        return resolved

    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Returns the active structured context for a session."""
        return self.structured_context.get(session_id, {})

    def add_turn(
        self,
        session_id: str,
        user_prompt: str,
        response_payload: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Appends a conversation turn to session memory."""
        turn = {
            "user_id": user_id or "default_user",
            "request_id": request_id,
            "prompt": user_prompt,
            "mode": response_payload.get("mode", "SQL_ANALYTICS"),
            "sql": response_payload.get("generated_sql") or response_payload.get("sql_query", ""),
            "summary": response_payload.get("summary") or response_payload.get("response", ""),
            "entities": response_payload.get("affected_tables", []),
            "context": self.structured_context.get(session_id, {}).copy()
        }

        self.sessions[session_id].append(turn)
        if len(self.sessions[session_id]) > self.max_turns:
            self.sessions[session_id] = self.sessions[session_id][-self.max_turns:]

    def get_history_turns(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns the history of turns for the given session."""
        return self.sessions.get(session_id, [])

    def get_history_summary(self, session_id: str) -> str:
        """Formats recent conversation history into concise text context for LLM prompt augmentation."""
        turns = self.get_history_turns(session_id)
        if not turns:
            return ""

        summary_lines = ["Recent Conversation Context:"]
        ctx = self.structured_context.get(session_id, {})
        if ctx:
            ctx_items = [f"{k}={v}" for k, v in ctx.items() if v and not k.startswith("time_condition")]
            if ctx_items:
                summary_lines.append(f"Active Session Context: {', '.join(ctx_items)}")

        for idx, t in enumerate(turns[-3:], 1):
            summary_lines.append(f"Turn {idx}: User asked '{t['prompt']}' | Mode: {t['mode']}")
            if t.get("sql"):
                summary_lines.append(f"  SQL Executed: {t['sql']}")

        return "\n".join(summary_lines)

    def clear_session(self, session_id: str):
        """Clears memory and structured context for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.structured_context:
            del self.structured_context[session_id]

memory_manager = MemoryManager()
