from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    interrupt_id: Optional[str] = None
    interrupt_description: Optional[str] = None
    interrupt_action: Optional[Dict[str, Any]] = None
    requires_approval: bool = False

class InterruptResolution(BaseModel):
    interrupt_id: str
    resolution: str
    thread_id: str

class InterruptApproval(BaseModel):
    interrupt_id: str
    approved: bool
    thread_id: str