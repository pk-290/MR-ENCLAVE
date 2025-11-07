from pydantic import BaseModel, Field
from typing import Any, Optional, Literal

# class SubscribeMsg(BaseModel):
#     type: Literal["subscribe"]
#     topic: str
#     last_n: Optional[int] = 0

# class UnsubscribeMsg(BaseModel):
#     type: Literal["unsubscribe"]
#     topic: str

# class PublishMsg(BaseModel):
#     type: Literal["publish"]
#     topic: str
#     payload: Any

# class PingMsg(BaseModel):
#     type: Literal["ping"]

# class EventOut(BaseModel):
#     type: Literal["event"] = "event"
#     topic: str
#     message: Any
#     timestamp: str = Field(..., description="ISO timestamp")
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal
from uuid import UUID

class MessagePayload(BaseModel):
    id: UUID
    payload: Any

class BaseWSIn(BaseModel):
    type: Literal["subscribe","unsubscribe","publish","ping"]
    request_id: Optional[str] = None

class SubscribeMsg(BaseWSIn):
    type: Literal["subscribe"]
    topic: str
    client_id: str
    last_n: Optional[int] = 0

class UnsubscribeMsg(BaseWSIn):
    type: Literal["unsubscribe"]
    topic: str
    client_id: str

class PublishMsg(BaseWSIn):
    type: Literal["publish"]
    topic: str
    message: MessagePayload

class PingMsg(BaseWSIn):
    type: Literal["ping"]