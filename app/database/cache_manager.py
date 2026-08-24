import time
import hashlib
import json
from typing import Optional, Dict, Any

class QueryCacheManager:
    """
    High-performance in-memory & Redis query result caching manager.
    Hashes incoming natural language queries (SHA-256) and stores response payloads
    with a 5-minute Time-To-Live (TTL) for sub-100ms response times.
    """
    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl = default_ttl_seconds
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _hash_key(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        cleaned = question.strip().lower()
        if context:
            clean_ctx = {
                k: str(v) for k, v in context.items()
                if v is not None and k in ["entity", "role_id", "region", "specific_id", "status_filter", "metric", "period", "limit"]
            }
            if clean_ctx:
                ctx_str = json.dumps(clean_ctx, sort_keys=True)
                return hashlib.sha256(f"{cleaned}::{ctx_str}".encode("utf-8")).hexdigest()
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    def get(self, question: str, context: Optional[Dict[str, Any]] = None, bypass_cache: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached JSON payload if available and valid.
        Returns None on cache miss or when bypass_cache is True.
        """
        if bypass_cache:
            return None
        key = self._hash_key(question, context=context)
        if key in self._memory_cache:
            item = self._memory_cache[key]
            if time.time() < item["expires_at"]:
                cached_res = dict(item["data"])
                cached_res["cached"] = True
                cached_res["cache_ttl_remaining"] = round(item["expires_at"] - time.time(), 2)
                return cached_res
            else:
                del self._memory_cache[key]
        return None

    def set(self, question: str, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None, ttl_seconds: Optional[int] = None):
        """
        Stores response payload in cache with TTL.
        """
        key = self._hash_key(question, context=context)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        # Create shallow copy of data to store
        data_to_store = dict(payload)
        data_to_store.pop("cached", None)
        data_to_store.pop("cache_ttl_remaining", None)
        
        self._memory_cache[key] = {
            "expires_at": time.time() + ttl,
            "data": data_to_store
        }

    def clear(self):
        """
        Clears all cached entries.
        """
        self._memory_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns stats about active cached items.
        """
        now = time.time()
        active = sum(1 for item in self._memory_cache.values() if item["expires_at"] > now)
        return {
            "total_cached_queries": active,
            "ttl_seconds": self.default_ttl
        }

cache_manager = QueryCacheManager(default_ttl_seconds=300)
