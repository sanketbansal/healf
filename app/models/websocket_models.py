from pydantic import BaseModel, ConfigDict
from typing import Dict, Any
from enum import Enum

class MessageType(str, Enum):
    INIT_PROFILE = "INIT_PROFILE"
    USER_ANSWER = "USER_ANSWER" 
    ASSISTANT_QUESTION = "ASSISTANT_QUESTION"
    PROFILE_COMPLETE = "PROFILE_COMPLETE"

class WebSocketMessage(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    type: MessageType
    data: Dict[str, Any]
    timestamp: str 