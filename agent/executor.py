import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
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
async def init_executor(model: BaseChatModel):        
    tools = await init_tools()
    
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt="""
You are Viettel Agent created by Viettel aim to support error handling and troubleshooting. You need to use the following tools to answer user queries.
Make sure to use the tools when needed, and provide clear and concise answers.

Notes:
**MCP** stands for **Model Context Protocol**
        """,
    )

    logger.info(f"Executor initialized with model={model.get_name()}")
    return agent

if __name__ == "__main__":
    import asyncio
    from langchain.chat_models import init_chat_model

    async def main():
        model = init_chat_model("openai:gpt-4.1-mini")
        executor = await init_executor(model)
        response = executor.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Show me all tools that you're provided"
                }
            ]
        })

        print(response['messages'][-1].content)

    
    asyncio.run(main())
