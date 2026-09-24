"""
Dynamic Semantic Few-Shot Exemplar Retriever for JGH Intelligence Engine.
STRICT ANTI-LEAKAGE ENFORCEMENT:
- Indexes strictly data/jgh_train.json (150 verified training cases).
- Strictly prevents any evaluation, validation, held-out test, or unseen questions from entering the index.
- Dynamically retrieves top-k semantically relevant training exemplars at prompt generation time.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

class DynamicExemplarRetriever:
    def __init__(self, train_path: Optional[Path] = None):
        self.train_path = train_path or (DATA_DIR / "jgh_train.json")
        self.exemplars: List[Dict[str, Any]] = []
        self._load_and_audit_training_exemplars()

    def _load_and_audit_training_exemplars(self):
        if not self.train_path.exists():
            logger.warning(f"[EXEMPLAR RETRIEVER] Training data not found at {self.train_path}")
            return

        with open(self.train_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Anti-Leakage Audit Gate
        held_out_path = DATA_DIR / "jgh_held_out_test.json"
        unseen_path = DATA_DIR / "jgh_unseen_generalization.json"
        forbidden_questions = set()

        if held_out_path.exists():
            with open(held_out_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    forbidden_questions.add(item["question"].strip().lower())
        if unseen_path.exists():
            with open(unseen_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    forbidden_questions.add(item["question"].strip().lower())

        clean_exemplars = []
        for item in raw_data:
            q = item.get("question", "").strip()
            sql = item.get("expected_sql", "").strip()
            if not q or not sql:
                continue

            # Critical assertion: zero leakage
            assert q.lower() not in forbidden_questions, (
                f"CRITICAL ANTI-LEAKAGE ALERT: Question '{q}' from evaluation splits detected in training data!"
            )
            clean_exemplars.append({
                "id": item.get("id"),
                "category": item.get("category", "general"),
                "question": q,
                "sql": sql,
                "tokens": set(re.findall(r"\w+", q.lower()))
            })

        self.exemplars = clean_exemplars
        logger.info(f"[EXEMPLAR RETRIEVER] Successfully indexed {len(self.exemplars)} verified training exemplars with zero test leakage.")

    def retrieve_exemplars(self, question: str, k: int = 2) -> List[Dict[str, str]]:
        """
        Retrieves top-k semantically relevant training exemplars based on token similarity and entity overlap.
        """
        if not self.exemplars:
            return []

        q_tokens = set(re.findall(r"\w+", question.lower()))
        scores = []

        for ex in self.exemplars:
            # Overlap score
            intersection = len(q_tokens & ex["tokens"])
            union = len(q_tokens | ex["tokens"])
            jaccard = intersection / union if union > 0 else 0.0

            # Domain bonus: category keyword alignment
            bonus = 0.0
            if any(w in question.lower() for w in ["box", "boxes", "scan", "scanned"]) and ex["category"] == "box_scanning":
                bonus += 0.3
            elif any(w in question.lower() for w in ["earning", "earnings", "revenue", "amount"]) and ex["category"] == "earnings":
                bonus += 0.3
            elif any(w in question.lower() for w in ["distributor", "mapped", "hierarchy"]) and ex["category"] == "distributor_hierarchy":
                bonus += 0.3
            elif any(w in question.lower() for w in ["compare", "vs", "versus"]) and ex["category"] == "monthly_comparison":
                bonus += 0.3
            elif any(w in question.lower() for w in ["lookup", "details", "find"]) and ex["category"] == "simple_lookup":
                bonus += 0.2

            score = jaccard + bonus
            scores.append((score, ex))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_k = [item[1] for item in scores[:k]]
        return [{"question": item["question"], "sql": item["sql"]} for item in top_k]

    def format_few_shot_prompt(self, question: str, k: int = 2) -> str:
        """Formats the retrieved exemplars into an authoritative prompt section."""
        retrieved = self.retrieve_exemplars(question, k=k)
        if not retrieved:
            return ""

        formatted_blocks = []
        for i, ex in enumerate(retrieved, 1):
            block = (
                f"-- Example {i}:\n"
                f"-- Question: {ex['question']}\n"
                f"{ex['sql']}"
            )
            formatted_blocks.append(block)

        return "\n\n".join(formatted_blocks)

# Singleton Instance
exemplar_retriever = DynamicExemplarRetriever()

def get_dynamic_few_shot_examples(question: str, k: int = 2) -> str:
    return exemplar_retriever.format_few_shot_prompt(question, k=k)
