from loguru import logger
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun

from .interruptor import add_human_in_the_loop
from dotenv import load_dotenv
import uuid
import os
import sys
import json

load_dotenv()

# ---- Logging setup ----
ENABLE_LOGGING = os.getenv("WORKFLOW_LOGGING", "1") == "1"
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

if ENABLE_LOGGING:
    logger.remove() 
    logger.add(
        f"{log_folder}/executor.json",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        enqueue=True,
        serialize=True,  
        backtrace=True,
        diagnose=True,
    )
else:
    logger.remove()

# ---- Executor ----
async def init_executor(llm_model: str = "gpt-4o-mini", **kwargs):    
    logger.info({"event": "init_executor_start", "model": llm_model})
    llm = ChatOpenAI(model=llm_model, **kwargs)
    
    client = MultiServerMCPClient(
        {
            "system-metrics-mcp": {
                "command": "python",
                "args": ["mcp_server.py"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()    
    search = DuckDuckGoSearchRun()        
    execute_command_tool = next(t for t in tools if t.name == "execute_command")
    other_tools = [t for t in tools if t.name != "execute_command"]

    wrapped_execute_command = add_human_in_the_loop(execute_command_tool)
    wrapped_search = add_human_in_the_loop(search)

    tools = other_tools + [wrapped_execute_command, wrapped_search]
    logger.info({"event": "tools_fetched", "tools": [t.name for t in tools]})

    memory = MemorySaver()
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt="""
You are a helpful assistant that uses the following tools to answer user queries.
Make sure to use the tools when needed, and provide clear and concise answers.

Notes:
**MCP** stands for **Model Context Protocol**
        """,
    )

    logger.success({"event": "agent_created"})
    return agent

# ---- Main ----
if __name__ == "__main__":
    import asyncio

    async def main():
        agent = await init_executor()
        config = RunnableConfig({
            "recursion_limit": 5,
            "thread_id": str(uuid.uuid4()),  # type: ignore
        })
        
        response = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content="List all MCP tools you can use."
                    )
                ]
            },
            config=config
        )
        logger.info({
            "event": "agent_response",
            "response": response['messages'][-1].content
        })
        print("Agent response:", response["messages"][-1].content)

    asyncio.run(main())
