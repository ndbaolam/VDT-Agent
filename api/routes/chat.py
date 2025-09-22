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
            response = await agent_service.chat(request)
            return response
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

    @router.post("/interrupt/approve")
    async def approve_interrupt(request: dict):
        """Approve or deny a pending interrupt"""
        try:
            logger.info(f"[approve_interrupt] Incoming request: {request}")

            interrupt_id = request.get("interrupt_id")
            approved = request.get("approved", False)
            thread_id = request.get("thread_id")

            logger.debug(f"[approve_interrupt] Extracted values -> "
                        f"interrupt_id={interrupt_id}, approved={approved}, thread_id={thread_id}")

            if not interrupt_id or not thread_id:
                logger.warning(f"[approve_interrupt] Missing required fields: "
                            f"interrupt_id={interrupt_id}, thread_id={thread_id}")
                raise ValueError("interrupt_id and thread_id are required")

            logger.info(f"[approve_interrupt] Calling agent_service.resolve_interrupt "
                        f"with interrupt_id={interrupt_id}, approved={approved}, thread_id={thread_id}")

            response = await agent_service.resolve_interrupt(
                interrupt_id,
                approved,
                thread_id
            )

            logger.info(f"[approve_interrupt] Resolution response: {response}")

            result = {
                "response": response,
                "thread_id": thread_id,
                "status": "resolved",
                "approved": approved
            }

            logger.info(f"[approve_interrupt] Final response: {result}")
            return result

        except ValueError as e:
            logger.error(f"[approve_interrupt] ValueError: {str(e)} | Request: {request}")
            raise HTTPException(status_code=404, detail=str(e))

        except Exception as e:
            logger.exception(f"[approve_interrupt] Unexpected error: {str(e)} | Request: {request}")
            raise HTTPException(status_code=500, detail=str(e))


    # Keep the old resolve endpoint for backward compatibility
    @router.post("/interrupt/resolve")
    async def resolve_interrupt(resolution: InterruptResolution):
        """Resolve a pending interrupt (legacy endpoint)"""
        try:
            # Convert old resolution format to approval format
            approved = resolution.resolution.lower() in ["approve", "yes", "true"]
            
            response = await agent_service.resolve_interrupt(
                resolution.interrupt_id,
                approved,
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