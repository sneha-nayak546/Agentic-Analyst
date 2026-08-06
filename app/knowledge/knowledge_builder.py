"""
Enterprise Knowledge Base Builder Script Orchestrator.
100% READ-ONLY operation against MySQL target database.

Executes complete knowledge discovery pipeline:
1. Schema & Column Metadata Extraction (INFORMATION_SCHEMA)
2. Foreign Key & Relationship Graph Discovery
3. DB Semantic Profiling & Master Lookup Table Row Sampling
4. Dynamic Business Dictionary Generation
5. Semantic Business Knowledge Graph Inversion & In-Memory Pre-indexing
"""
import os
import json
import time

from app.database.schema_extractor import extract_db_schema
from app.knowledge.relationship_builder import get_relationship_graph
from app.knowledge.db_profiler import run_database_profiler
from app.knowledge.knowledge_graph import get_knowledge_graph


def rebuild_complete_knowledge_base():
    t0 = time.time()
    print("=" * 70)
    print("     STARTING REBUILD OF READ-ONLY ENTERPRISE KNOWLEDGE BASE")
    print("=" * 70)

    # 1. Extract DB Schema Metadata
    print("\n[STEP 1/4] Extracting Database Schema Metadata...")
    schema = extract_db_schema()
    print(f" -> Successfully extracted metadata for {len(schema)} target tables.")

    # 2. Discover Relationships
    print("\n[STEP 2/4] Discovering Foreign Keys & Table Relationships...")
    relationships = get_relationship_graph()
    print(f" -> Successfully mapped {len(relationships)} foreign key join edges.")

    # 3. Profile DB & Build Business Dictionary
    print("\n[STEP 3/4] Profiling Master/Lookup Tables & Generating Business Dictionary...")
    profile = run_database_profiler()
    vocab_count = len(profile.get("business_terminology", {}))
    print(f" -> Successfully indexed {vocab_count} dynamic business vocabulary terms.")

    # 4. Refresh In-Memory Knowledge Graph
    print("\n[STEP 4/4] Building Semantic Business Knowledge Graph...")
    kg = get_knowledge_graph()
    kg.load_metadata()
    kg.build_graph()
    print(" -> Knowledge Graph populated with O(1) in-memory term resolver.")

    total_time = round((time.time() - t0) * 1000, 2)
    print("\n" + "=" * 70)
    print(f" [SUCCESS] KNOWLEDGE BASE REBUILD COMPLETED IN {total_time} ms")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    rebuild_complete_knowledge_base()

