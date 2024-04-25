from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Part(BaseModel):
    content: str
    role: str

class MetaContent(BaseModel):
    # conversation: List[Dict[str, Any]] = []
    # internet_access: bool = Field(default=False)
    # content_type: str = Field(default="text")
    parts: List[Part]

class Meta(BaseModel):
    id: int
    content: MetaContent

class ConversationRequest(BaseModel):
    conversation_id: str
    action: str
    model: str
    jailbreak: str
    meta: Meta