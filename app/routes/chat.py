from fastapi import APIRouter
from app.models import ChatRequest, ChatResponse, ResumeRequest
from app.services.chat import process_chat, resume_chat

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    thread_id, result, interrupt_data = await process_chat(req.input)
    return ChatResponse(thread_id=thread_id, result=result, interrupt=interrupt_data)

@router.post("/resume", response_model=ChatResponse)
async def resume(req: ResumeRequest):
    result = await resume_chat(req.thread_id, req.decision)
    return ChatResponse(thread_id=req.thread_id, result=result, interrupt=None)
