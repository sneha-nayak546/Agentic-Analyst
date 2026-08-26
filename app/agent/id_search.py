import re
from typing import Dict, Any, Tuple
from app.database.read_executor import execute_read_query
from app.agent.business_requirement import BusinessRequirement

INVALID_ID_CHARS = set("@!#$%^&*~+=/\\?<>{}[]|")

def validate_id_format(raw_id: str, entity_name: str = "ID") -> Tuple[bool, str]:
    raw_id_str = str(raw_id)
    if any(char in raw_id_str for char in INVALID_ID_CHARS):
        return False, f'"{raw_id}" is not a valid {entity_name.capitalize()} format.'
    if not re.match(r"^[0-9a-zA-Z_\-]+$", raw_id_str):
        return False, f'"{raw_id}" is not a valid {entity_name.capitalize()} format.'
    return True, ""

def extract_id_from_prompt(prompt: str, skip_intent_check: bool = False) -> Dict[str, Any]:
    """Extracts a potential ID from the user prompt."""
    m = re.search(r'\b(distributor|retailer|wholesaler|user|company)?\s*(?:id|code)?\s*(\d{3,7})\b', prompt, re.IGNORECASE)
    if m:
        entity = m.group(1).lower() if m.group(1) else "user"
        raw_id = m.group(2)
        return {"has_id": True, "raw_id": raw_id, "entity": entity}
    
    if skip_intent_check:
        m2 = re.search(r'\b(\d{3,7})\b', prompt)
        if m2:
            return {"has_id": True, "raw_id": m2.group(1), "entity": "user"}
            
    return {"has_id": False}


def resolve_entities_and_ids(req: BusinessRequirement) -> Dict[str, Any]:
    """
    Phase 4: Entity and ID Resolution
    Takes the canonical BusinessRequirement and validates all specific IDs against the DB.
    Returns a resolution object. If an ID is missing, it returns a halted status with suggestions.
    """
    resolution_context = {
        "status": "success",
        "resolved_ids": {},
        "missing_ids": [],
        "error_message": None
    }
    
    if not req.specific_ids:
        return resolution_context

    for id_key, raw_id in req.specific_ids.items():
        is_valid, err_msg = validate_id_format(raw_id, id_key)
        if not is_valid:
            resolution_context["status"] = "halted"
            resolution_context["error_message"] = err_msg
            return resolution_context
            
        int_id = None
        try:
            int_id = int(raw_id)
        except ValueError:
            pass

        # Determine table based on id_key
        table = "users"
        role_filter = ""
        if "distributor" in id_key:
            role_filter = "AND user_role = 4"
        elif "retailer" in id_key:
            role_filter = "AND user_role = 2"
        elif "wholesaler" in id_key:
            role_filter = "AND user_role = 5"
            
        if int_id is not None:
            # Check users table
            sql = f"SELECT id, name FROM {table} WHERE id = {int_id} {role_filter} LIMIT 1;"
            res = execute_read_query(sql)
            
            if res.get("data") and len(res["data"]) > 0:
                resolution_context["resolved_ids"][id_key] = {
                    "raw_id": int_id,
                    "name": res["data"][0].get("name")
                }
            else:
                # If distributor, check companies table for master code
                if "distributor" in id_key or "sap" in id_key:
                    comp_sql = f"SELECT id, name FROM companies WHERE id = {int_id} LIMIT 1;"
                    comp_res = execute_read_query(comp_sql)
                    if comp_res.get("data") and len(comp_res["data"]) > 0:
                        resolution_context["resolved_ids"][id_key] = {
                            "raw_id": int_id,
                            "name": comp_res["data"][0].get("name"),
                            "is_company_code": True
                        }
                        continue
                        
                # Not found. Find suggestions.
                resolution_context["status"] = "halted"
                resolution_context["missing_ids"].append(id_key)
                
                # Fetch nearest IDs
                sugg_sql = f"SELECT id, name FROM {table} WHERE 1=1 {role_filter} ORDER BY ABS(id - {int_id}) ASC LIMIT 3;"
                sugg_res = execute_read_query(sugg_sql)
                suggestions = [str(r["id"]) for r in sugg_res.get("data", [])]
                
                ent_name = id_key.replace('_id', '').capitalize()
                err = f"{ent_name} ID {raw_id} was not found."
                if suggestions:
                    sugg_str = ", ".join(suggestions)
                    err += f" Did you mean one of these: {sugg_str}?"
                resolution_context["error_message"] = err
                return resolution_context
        else:
            # Alphanumeric ID (like referral codes)
            sql = f"SELECT id, name FROM users WHERE referral_code = '{raw_id}' OR mobile_number = '{raw_id}' LIMIT 1;"
            res = execute_read_query(sql)
            if res.get("data") and len(res["data"]) > 0:
                resolution_context["resolved_ids"][id_key] = {
                    "raw_id": res["data"][0].get("id"),
                    "name": res["data"][0].get("name")
                }
            else:
                resolution_context["status"] = "halted"
                resolution_context["error_message"] = f"Identifier {raw_id} was not found in the database."
                return resolution_context

    return resolution_context
