from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ConversationRequest(BaseModel):
    conversation_id: str
    content: str
    suggested: int
    
class ReportRequest(BaseModel):
    conversation_id: str
    content: str
    username: str