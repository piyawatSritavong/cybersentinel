from typing import Dict, Any, Optional
from pydantic import BaseModel
import json

class StandardLog(BaseModel):
    """
    Standard schema based loosely on OCSF.
    """
    original_id: str
    source_type: str
    timestamp: str
    event_type: str
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    user: Optional[str] = None
    severity: str
    raw_data: str

class Normalizer:
    @staticmethod
    def to_ocsf(raw_log: Dict[str, Any], source: str) -> StandardLog:
        """
        Normalize logs from different SIEMs/sources to a standard OCSF-like format.
        """
        if source.lower() == "splunk":
            return StandardLog(
                original_id=raw_log.get("alert_id", "unknown"),
                source_type="splunk",
                timestamp=raw_log.get("timestamp", ""),
                event_type=raw_log.get("description", "unknown"),
                severity=str(raw_log.get("risk_score", "medium")),
                raw_data=json.dumps(raw_log)
            )
        elif source.lower() == "paloalto":
            return StandardLog(
                original_id=raw_log.get("log_id", "unknown"),
                source_type="paloalto",
                timestamp=raw_log.get("time_generated", ""),
                event_type=raw_log.get("type", "unknown"),
                src_ip=raw_log.get("src", ""),
                dst_ip=raw_log.get("dst", ""),
                severity=raw_log.get("severity", "medium"),
                raw_data=json.dumps(raw_log)
            )
        elif source.lower() == "crowdstrike":
            return StandardLog(
                original_id=raw_log.get("detect_id", "unknown"),
                source_type="crowdstrike",
                timestamp=raw_log.get("timestamp", ""),
                event_type=raw_log.get("tactic", "unknown"),
                user=raw_log.get("user_name", ""),
                severity=raw_log.get("severity", "medium"),
                raw_data=json.dumps(raw_log)
            )
        else:
            return StandardLog(
                original_id=raw_log.get("id", "unknown"),
                source_type=source,
                timestamp=raw_log.get("timestamp", ""),
                event_type=raw_log.get("event", "unknown"),
                severity="unknown",
                raw_data=json.dumps(raw_log)
            )
