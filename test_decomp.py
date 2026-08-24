from app.agent.query_decomposer import decompose_query
q = "Generate a table of retailers linked to distributor 5997, and include a column for their individual total earnings for the current month."
res = decompose_query(q)
print("DECOMPOSED:", res)
