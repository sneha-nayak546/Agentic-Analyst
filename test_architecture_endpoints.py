"""
Verification script for System Architecture telemetry and query simulation endpoints.
"""

import sys
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_architecture_endpoints():
    print("=" * 70)
    print("      TESTING SYSTEM ARCHITECTURE TELEMETRY & SIMULATOR")
    print("=" * 70)

    # 1. Test /api/architecture/status
    print("\n[1/3] Testing GET /api/architecture/status...")
    res = client.get("/api/architecture/status")
    assert res.status_code == 200, f"Status failed: {res.status_code}"
    data = res.json()
    assert data.get("status") == "HEALTHY"
    arch = data.get("architecture", {})
    
    assert "users_layer" in arch
    assert "load_balancer" in arch
    assert "api_gateway" in arch
    assert "semantic_cache" in arch
    assert "model_orchestration" in arch
    assert "validation_gate" in arch
    assert "data_layer" in arch
    assert "infrastructure" in arch

    # Check 5 validation gates
    gates = arch["validation_gate"]["gates"]
    gate_ids = [g["id"] for g in gates]
    assert "dict_lookup" in gate_ids
    assert "role_fk" in gate_ids
    assert "blacklist" in gate_ids
    assert "explain_cost" in gate_ids
    assert "schema_drift" in gate_ids
    print(f"  -> All 8 architecture tiers & 5 validation gates verified healthy!")

    # 2. Test /api/architecture/simulate with SQL Analytics query
    print("\n[2/3] Testing POST /api/architecture/simulate (SQL Analytics query)...")
    sim_res = client.post("/api/architecture/simulate", json={
        "question": "Show top 5 retailers by earnings for July 2026",
        "bypass_cache": True
    })
    assert sim_res.status_code == 200, f"Simulate failed: {sim_res.status_code}"
    sim_data = sim_res.json()
    assert len(sim_data.get("trace_steps", [])) >= 5
    assert sim_data.get("detected_mode") == "SQL_ANALYTICS"
    assert sim_data.get("generated_sql") != ""
    print(f"  -> Live trace completed in {sim_data.get('total_latency_ms')} ms with {len(sim_data['trace_steps'])} steps.")

    # 3. Test /api/architecture/simulate with Tutor QA query
    print("\n[3/3] Testing POST /api/architecture/simulate (Tutor QA query)...")
    sim_res2 = client.post("/api/architecture/simulate", json={
        "question": "explain about retailer",
        "bypass_cache": True
    })
    assert sim_res2.status_code == 200
    sim_data2 = sim_res2.json()
    assert sim_data2.get("detected_mode") == "TUTOR_QA"
    assert "Retailer" in sim_data2.get("response", "")
    print(f"  -> Tutor trace completed in {sim_data2.get('total_latency_ms')} ms!")

    print("\n" + "=" * 70)
    print("  [SYSTEM ARCHITECTURE BLUEPRINT & SIMULATOR PASSED 100%!]")
    print("=" * 70)

if __name__ == "__main__":
    test_architecture_endpoints()
