from typing import Dict, List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    model: Optional[str] = "openai:gpt-4o-mini"
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    thread_id: str

class InterruptResponse(BaseModel):
    interrupt_id: str
    description: str
    action_request: Dict
    thread_id: str

class InterruptResolution(BaseModel):
    interrupt_id: str
    resolution: str  # "y" or "n"
    thread_id: str

class ThreadStatus(BaseModel):
    thread_id: str
    status: str
    message_count: int

class ErrorResponse(BaseModel):
    detail: str
    error_type: str
    thread_id: Optional[str] = None

