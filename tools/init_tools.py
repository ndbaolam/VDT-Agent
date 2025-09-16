import os, sys
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_community.tools import DuckDuckGoSearchRun
from .interruptor import add_human_in_the_loop
from .retriever import get_retriever_tool
from dotenv import load_dotenv

load_dotenv()

MCP_URL = os.getenv("MCP_HOST", "http://localhost:8000/mcp")

async def init_tools():
    try: 
        client = MultiServerMCPClient(
            {
                "system-metrics-mcp": {
                    "command": "python",
                    "args": ["tools/mcp_server.py"],
                    "transport": "stdio",
                }
            }
        )
    except:
        client = MultiServerMCPClient(
            {
                "system-metrics-mcp": {
                    "url": MCP_URL,
                    "transport": "streamable_http",
                }
            }
        )

    tools = await client.get_tools()    
    search = DuckDuckGoSearchRun()        
    retriever_tool =  get_retriever_tool()
    execute_command_tool = next(t for t in tools if t.name == "execute_command")
    other_tools = [t for t in tools if t.name != "execute_command"]

    wrapped_execute_command = add_human_in_the_loop(execute_command_tool)
    wrapped_search = add_human_in_the_loop(search)

    tools = other_tools + [wrapped_execute_command, wrapped_search, retriever_tool]

    return tools

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_tools())