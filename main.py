import uvicorn
from app.config import create_app
from app.routes import chat
from app.services.chat import init_agents

app = create_app()

# Register routes
app.include_router(chat.router)

@app.on_event("startup")
async def startup_event():
    await init_agents()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
    )
