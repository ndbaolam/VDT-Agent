import os
from loguru import logger

class Config:
    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 3000
    API_RELOAD = True
    LOG_LEVEL = "info"
    
    # Model Configuration
    DEFAULT_MODEL = "openai:gpt-4o-mini"
    DEFAULT_TEMPERATURE = 0
    MAX_TOKENS = 1024
    RECURSION_LIMIT = 10
    
    # Logging Configuration
    LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
    LOG_FILE = os.path.join(LOG_DIR, "api.log")
    LOG_ROTATION = "10 MB"
    LOG_RETENTION = "10 days"
    LOG_COMPRESSION = "zip"

def setup_logging():
    """Configure logging for the application"""
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    logger.remove()
    logger.add(
        Config.LOG_FILE,
        rotation=Config.LOG_ROTATION,
        retention=Config.LOG_RETENTION,
        compression=Config.LOG_COMPRESSION,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )