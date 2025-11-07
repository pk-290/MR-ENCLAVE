# from datetime import datetime, timezone

# def now_ts():
#     return datetime.now(timezone.utc).isoformat()

# def make_ack(request_id=None, topic=None, status="ok"):
#     out = {"type":"ack", "status": status, "ts": now_ts()}
#     if request_id: out["request_id"] = request_id
#     if topic: out["topic"] = topic
#     return out

# def make_event(topic, message, request_id=None):
#     return {
#         "type": "event",
#         "topic": topic,
#         "message": {"id": str(message["id"]), "payload": message["payload"]},
#         "ts": now_ts(),
#         **({"request_id": request_id} if request_id else {})
#     }

# def make_error(code, message, request_id=None, topic=None):
#     e = {"type":"error", "error":{"code": code, "message": message}, "ts": now_ts()}
#     if request_id: e["request_id"] = request_id
#     if topic: e["topic"] = topic
#     return e

# def make_pong(request_id=None):
#     out = {"type": "pong", "ts": now_ts()}
#     if request_id: out["request_id"] = request_id
#     return out

# def make_info(msg, topic=None):
#     out = {"type":"info", "msg": msg, "ts": now_ts()}
#     if topic: out["topic"] = topic
#     return out

# app/utils/util.py
import time
from typing import Optional, Any, Dict

def now_ts() -> str:
    """Return ISO timestamp (UTC)."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def make_ack(request_id: Optional[str], topic: Optional[str], status: str = "ok") -> Dict[str, Any]:
    out = {"type": "ack", "status": status, "ts": now_ts()}
    if request_id:
        out["request_id"] = request_id
    if topic:
        out["topic"] = topic
    return out

def make_error(code: str, message: str, request_id: Optional[str] = None, topic: Optional[str] = None) -> Dict[str, Any]:
    out = {
        "type": "error",
        "error": {"code": code, "message": message},
        "ts": now_ts()
    }
    if request_id:
        out["request_id"] = request_id
    if topic:
        out["topic"] = topic
    return out

def make_event(topic: str, message: Any, request_id: Optional[str] = None) -> Dict[str, Any]:
    out = {
        "type": "event",
        "topic": topic,
        "message": message,
        "ts": now_ts()
    }
    if request_id:
        out["request_id"] = request_id
    return out

def make_pong(request_id: Optional[str] = None) -> Dict[str, Any]:
    out = {"type": "pong", "ts": now_ts()}
    if request_id:
        out["request_id"] = request_id
    return out

def make_info(msg: str, topic: Optional[str] = None) -> Dict[str, Any]:
    out = {"type": "info", "msg": msg, "ts": now_ts()}
    if topic:
        out["topic"] = topic
    return out