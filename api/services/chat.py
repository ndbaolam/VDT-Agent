import os
import sys
import uuid
from typing import Dict, Any, AsyncGenerator, Tuple, Optional

from api.config import Config
from api.models import ChatRequest, ChatResponse

# Import the workflow
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from agent.workflow import build_graph
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from loguru import logger

class AgentService:
    def __init__(self):
        self.graph = None
        self.active_threads: Dict[str, Dict] = {}
        self.pending_interrupts: Dict[str, Dict] = {}
    
    async def initialize(self):
        """Initialize the agent graph"""
        if self.graph is None:
            logger.info("Initializing agent graph...")
            self.graph = await build_graph()
            logger.info("Agent graph initialized successfully")
    
    async def chat(self, request: ChatRequest) -> Tuple[ChatResponse, Optional[str]]:
        """Process a chat request and return response"""
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Track thread
        self.active_threads[thread_id] = {
            "status": "processing",
            "message_count": self.active_threads.get(thread_id, {}).get("message_count", 0) + 1
        }
        
        config: RunnableConfig = {
            "recursion_limit": Config.RECURSION_LIMIT,
            "thread_id": thread_id,
        }
        
        response_content = ""
        interrupt_id = None
        
        try:
            async for chunk in self.graph.astream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
            ):
                if "__interrupt__" in chunk:
                    interrupts = chunk.get("__interrupt__") or []
                    interrupt = interrupts[0] if interrupts else None
                    if interrupt:
                        interrupt_id = str(uuid.uuid4())
                        self.pending_interrupts[interrupt_id] = {
                            "thread_id": thread_id,
                            "interrupt": interrupt,
                            "config": config
                        }
                        self.active_threads[thread_id]["status"] = "interrupted"
                        break
                else:
                    for node_name, node_data in chunk.items():
                        if "messages" in node_data:
                            if hasattr(node_data['messages'], 'content'):
                                response_content += node_data['messages'].content
            
            if not interrupt_id:
                self.active_threads[thread_id]["status"] = "completed"
            
            return ChatResponse(response=response_content, thread_id=thread_id), interrupt_id
            
        except Exception as e:
            self.active_threads[thread_id]["status"] = "error"
            logger.error(f"Error in chat processing: {str(e)}")
            raise
    
    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Stream chat responses"""
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Track thread
        self.active_threads[thread_id] = {
            "status": "streaming",
            "message_count": self.active_threads.get(thread_id, {}).get("message_count", 0) + 1
        }
        
        config: RunnableConfig = {
            "recursion_limit": Config.RECURSION_LIMIT,
            "thread_id": thread_id,
        }
        
        try:
            async for chunk in self.graph.astream(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
            ):
                if "__interrupt__" in chunk:
                    interrupts = chunk.get("__interrupt__") or []
                    interrupt = interrupts[0] if interrupts else None
                    if interrupt:
                        interrupt_id = str(uuid.uuid4())
                        self.pending_interrupts[interrupt_id] = {
                            "thread_id": thread_id,
                            "interrupt": interrupt,
                            "config": config
                        }
                        self.active_threads[thread_id]["status"] = "interrupted"
                        yield f"data: {{'type': 'interrupt', 'interrupt_id': '{interrupt_id}', 'description': '{interrupt.value.get('description')}'}}\n\n"
                        break
                else:
                    for node_name, node_data in chunk.items():
                        if "messages" in node_data:
                            if hasattr(node_data['messages'], 'content'):
                                content = str(node_data['messages'].content).replace('"', '\\"')
                                yield f'data: {{"type": "content", "content": "{content}"}}\n\n'
            
            if thread_id in self.active_threads and self.active_threads[thread_id]["status"] != "interrupted":
                self.active_threads[thread_id]["status"] = "completed"
                yield f'data: {{"type": "done", "thread_id": "{thread_id}"}}\n\n'
            
        except Exception as e:
            self.active_threads[thread_id]["status"] = "error"
            logger.error(f"Error in streaming: {str(e)}")
            yield f'data: {{"type": "error", "error": "{str(e)}"}}\n\n'
    
    async def resolve_interrupt(self, interrupt_id: str, resolution: str, thread_id: str) -> str:
        """Resolve a pending interrupt"""
        if interrupt_id not in self.pending_interrupts:
            raise ValueError("Interrupt not found")
        
        interrupt_data = self.pending_interrupts[interrupt_id]
        config = interrupt_data["config"]
        
        response_content = ""
        
        try:
            self.active_threads[thread_id]["status"] = "resolving"
            
            async for message_chunk, metadata in self.graph.astream(
                Command(resume={"type": resolution}),
                stream_mode="messages",
                config=config,
            ):
                if message_chunk.content:
                    response_content += message_chunk.content
            
            # Clean up
            del self.pending_interrupts[interrupt_id]
            self.active_threads[thread_id]["status"] = "completed"
            
            return response_content
            
        except Exception as e:
            self.active_threads[thread_id]["status"] = "error"
            logger.error(f"Error resolving interrupt: {str(e)}")
            raise
    
    def get_interrupt(self, interrupt_id: str) -> Optional[Dict]:
        """Get interrupt details"""
        interrupt_data = self.pending_interrupts.get(interrupt_id)
        if not interrupt_data:
            return None
        
        return {
            "interrupt_id": interrupt_id,
            "thread_id": interrupt_data["thread_id"],
            "description": interrupt_data["interrupt"].value.get("description"),
            "action_request": interrupt_data["interrupt"].value.get("action_request", {})
        }
    
    def get_all_interrupts(self) -> list:
        """Get all pending interrupts"""
        return [
            {
                "interrupt_id": interrupt_id,
                "thread_id": data["thread_id"],
                "description": data["interrupt"].value.get("description"),
                "action_request": data["interrupt"].value.get("action_request", {})
            }
            for interrupt_id, data in self.pending_interrupts.items()
        ]
    
    def get_thread_status(self, thread_id: str) -> Optional[Dict]:
        """Get thread status"""
        return self.active_threads.get(thread_id)
    
    def get_all_threads(self) -> Dict[str, Dict]:
        """Get all threads"""
        return self.active_threads
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and clean up"""
        deleted = False
        
        if thread_id in self.active_threads:
            del self.active_threads[thread_id]
            deleted = True
        
        # Clean up interrupts for this thread
        to_remove = [
            interrupt_id for interrupt_id, data in self.pending_interrupts.items()
            if data["thread_id"] == thread_id
        ]
        for interrupt_id in to_remove:
            del self.pending_interrupts[interrupt_id]
            deleted = True
        
        return deleted