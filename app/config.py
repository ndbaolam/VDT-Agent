from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

def create_app() -> FastAPI:
    app = FastAPI(title="Agent API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("✅ App created successfully.")
    return app
