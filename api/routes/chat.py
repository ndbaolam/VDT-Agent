from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from api.models import ChatRequest, ChatResponse, InterruptResolution
from api.services import AgentService

def create_router(agent_service: AgentService) -> APIRouter:
    router = APIRouter()
    
    @router.get("/")
    async def root():
        return {"message": "LangGraph Agent API is running"}
    
    @router.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "active_threads": len(agent_service.get_all_threads()),
            "pending_interrupts": len(agent_service.get_all_interrupts())
        }
    
    @router.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Send a message to the agent"""
        try:
            response, interrupt_id = await agent_service.chat(request)
            
            if interrupt_id:
                interrupt_info = agent_service.get_interrupt(interrupt_id)
                raise HTTPException(
                    status_code=202,
                    detail={
                        "type": "interrupt",
                        **interrupt_info
                    }
                )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/chat/stream")
    async def stream_chat(request: ChatRequest):
        """Stream chat responses"""
        return StreamingResponse(
            agent_service.stream_chat(request),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    
    @router.post("/interrupt/resolve")
    async def resolve_interrupt(resolution: InterruptResolution):
        """Resolve a pending interrupt"""
        try:
            response = await agent_service.resolve_interrupt(
                resolution.interrupt_id,
                resolution.resolution,
                resolution.thread_id
            )
            
            return {
                "response": response,
                "thread_id": resolution.thread_id,
                "status": "resolved"
            }
            
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Interrupt resolution error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/interrupts")
    async def get_interrupts():
        """Get all pending interrupts"""
        return {"interrupts": agent_service.get_all_interrupts()}
    
    @router.get("/threads")
    async def get_threads():
        """Get all active threads"""
        return {"threads": agent_service.get_all_threads()}
    
    @router.get("/threads/{thread_id}")
    async def get_thread_status(thread_id: str):
        """Get specific thread status"""
        thread_status = agent_service.get_thread_status(thread_id)
        if not thread_status:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {"thread_id": thread_id, **thread_status}
    
    @router.delete("/threads/{thread_id}")
    async def delete_thread(thread_id: str):
        """Delete a thread"""
        deleted = agent_service.delete_thread(thread_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {"message": f"Thread {thread_id} deleted successfully"}
    
    return router
