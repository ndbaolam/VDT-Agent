import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools.interruptor import add_human_in_the_loop
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

MCP_URL = os.getenv("MCP_HOST", "http://localhost:8000/mcp")

class ExecutorResponse(BaseModel):
    answer: str = Field(..., description="The final answer provided by the agent.")
    thought_process: List[str] = Field(..., description="List of thoughts and actions taken by the agent.")

# ---- Executor ----
async def init_tools():
    client = MultiServerMCPClient(
            {
                "system-metrics-mcp": {
                    "url": MCP_URL,
                    "transport": "streamable_http",
                }
            }
        )

    tools = await client.get_tools()    

    execute_command_tool = next(t for t in tools if t.name == "execute_command")
    other_tools = [t for t in tools if t.name != "execute_command"]

    wrapped_execute_command = add_human_in_the_loop(execute_command_tool)

    return [wrapped_execute_command, *other_tools]


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
        response_format=ExecutorResponse,
        name="executor",
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

        print(response["structured_response"])
    
    asyncio.run(main())