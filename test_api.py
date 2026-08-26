import traceback
from app.api.main import query_database, QueryRequest
try:
    query_database(QueryRequest(question='58997 under this distributor how many retailers are available and give me those retailers in this month earnings'))
except Exception as e:
    traceback.print_exc()
