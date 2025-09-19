from fastapi import FastAPI
from loguru import logger

from api.config import Config, setup_logging
from api.services import AgentService
from api.routes import create_router

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="LangGraph Agent API",
    description="Simple API for LangGraph agents",
    version="1.0.0"
)

# Global service
agent_service = AgentService()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting FastAPI server...")
    await agent_service.initialize()
    
    # Add routes
    router = create_router(agent_service)
    app.include_router(router)
    
    logger.info("Server started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.API_RELOAD,
        log_level=Config.LOG_LEVEL
    )