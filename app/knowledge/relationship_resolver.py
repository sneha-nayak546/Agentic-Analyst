import logging
from typing import Dict, Any, List

from app.knowledge.table_schemas import JOIN_DEFINITIONS, TABLE_SUMMARIES

logger = logging.getLogger(__name__)

class RelationshipResolver:
    """
    Verifies and resolves business relationships between entities before SQL generation.
    Enforces the rule: NEVER guess the join. If a relationship cannot be verified, abort.
    """

    def resolve_relationships(self, structured_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes the output from NLPIntentParser and verifies all requested relationships.
        Modifies structured_plan in place to add verified_join_paths.
        """
        entities = set(structured_plan.get("entities", []))
        if structured_plan.get("primary_entity"):
            entities.add(structured_plan["primary_entity"])
            
        # If specific ID type implies a relationship (e.g. distributor ID looking for retailers)
        spec_id = structured_plan.get("specific_id", {})
        id_type = spec_id.get("type")
        if id_type and id_type != structured_plan.get("primary_entity"):
             if id_type not in entities:
                 entities.add(id_type)

        # Basic entity mapping
        mapped_tables = set()
        for e in entities:
            if not e: continue
            e_clean = e.lower().strip()
            # Handle common aliases
            if e_clean in ["retailer", "distributor", "mechanic", "wholesaler", "user", "retailers", "distributors"]:
                mapped_tables.add("users")
            elif e_clean in ["transaction", "earnings", "wallet_transaction"]:
                mapped_tables.add("wallet_transaction")
            elif e_clean in ["withdrawal", "withdrawal_request"]:
                mapped_tables.add("withdrawal_request")
            elif e_clean in ["sku", "inventory", "sku_inventories"]:
                mapped_tables.add("sku_inventories")
            else:
                mapped_tables.add(e_clean)

        structured_plan["verified_tables"] = list(mapped_tables)
        verified_joins = []

        if len(mapped_tables) > 1:
            # We need to verify that all tables are connected
            table_list = list(mapped_tables)
            for i in range(len(table_list)):
                for j in range(i + 1, len(table_list)):
                    t1, t2 = table_list[i], table_list[j]
                    found_join = False
                    for jt1, jt2, join_str in JOIN_DEFINITIONS:
                        if (t1 == jt1 and t2 == jt2) or (t1 == jt2 and t2 == jt1):
                            verified_joins.append(join_str)
                            found_join = True
                            break
                    
                    # Special Case: user hierarchy joins (distributor to retailer)
                    if t1 == "users" and t2 == "users":
                        if "distributor" in entities and "retailer" in entities:
                            verified_joins.append("users as dist JOIN users as ret ON dist.id = ret.distributer_id")
                            found_join = True

        structured_plan["verified_join_paths"] = verified_joins
        
        # Check if requested relationships are missing
        if len(mapped_tables) > 1 and not verified_joins:
            structured_plan["relationship_error"] = f"Could not verify a business relationship between {list(mapped_tables)}."
            structured_plan["confidence"] = 0

        return structured_plan

relationship_resolver = RelationshipResolver()
