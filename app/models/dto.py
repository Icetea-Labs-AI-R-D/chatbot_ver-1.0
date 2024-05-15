from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Part(BaseModel):
    content: str
    role: str

class MetaContent(BaseModel):
    parts: List[Part]

class Meta(BaseModel):
    content: MetaContent

class ConversationRequest(BaseModel):
    conversation_id: str
    action: str
    meta: Meta