import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from tools import init_tools
from dotenv import load_dotenv

load_dotenv()

# ---- Logging config ----
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "all.log")

logger.remove() 
logger.add(
    LOG_FILE,
    rotation="10 MB",   
    retention="10 days", 
    compression="zip",   
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

# ---- Executor ----
async def init_executor(llm_model: str = "openai:gpt-4o-mini", **kwargs):    
    llm = init_chat_model(llm_model, temperature=0)
    
    tools = await init_tools()
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt="""
You are a helpful assistant that uses the following tools to answer user queries.
Make sure to use the tools when needed, and provide clear and concise answers.

Notes:
**MCP** stands for **Model Context Protocol**
        """,
        checkpointer=InMemorySaver()
    )

    logger.info(f"Executor initialized with model={llm_model}")
    return agent
