"""
Incognito Privacy Controller for JGH Intelligence Engine.
Manages ephemeral privacy mode (is_private == true):
  - Suppresses disk logging to query_audit.json, execution_history.json, and session logs.
  - Keeps request processing transient in RAM.
"""

from typing import Dict, Any, Optional

class PrivacyManager:
    @staticmethod
    def is_private_request(request_data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> bool:
        """
        Detects if a request has incognito/private mode enabled via payload flag or HTTP header.
        """
        if request_data and isinstance(request_data, dict):
            if request_data.get("is_private") or request_data.get("incognito"):
                return True
        if headers:
            header_val = headers.get("x-incognito-mode") or headers.get("x-private-mode")
            if header_val and header_val.lower() in ["true", "1", "yes"]:
                return True
        return False

    @staticmethod
    def should_log(is_private: bool) -> bool:
        """Returns True if logging is allowed, False if suppressed by privacy mode."""
        return not is_private

privacy_manager = PrivacyManager()
