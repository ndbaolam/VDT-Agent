from typing import Dict, Any
from pydantic import BaseModel

class ChatRequest(BaseModel):
    input: str

class ChatResponse(BaseModel):
    thread_id: str
    result: Any
    interrupt: Dict[str, Any] | None = None

class ResumeRequest(BaseModel):
    thread_id: str
    decision: str  # "y" or "n"
