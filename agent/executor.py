import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.caches import InMemoryCache
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.memory import InMemorySaver
from agent.interruptor import add_human_in_the_loop
from dotenv import load_dotenv
import uuid

load_dotenv()

ENABLE_LOGGING = os.getenv("WORKFLOW_LOGGING", "1") == "1"
MCP_URL = os.getenv("MCP_HOST", "http://localhost:8000/mcp")

# ---- Logging setup ----
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

    try:
        llm = ChatOpenAI(
            model=llm_model,
            cache=InMemoryCache(),
            **kwargs
        )
    except:
        llm = ChatOllama(
            model=llm_model,
            cache=InMemoryCache(),
            **kwargs
        )

    try: 
        client = MultiServerMCPClient(
            {
                "system-metrics-mcp": {
                    "command": "python",
                    "args": ["mcp_server.py"],
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
    execute_command_tool = next(t for t in tools if t.name == "execute_command")
    other_tools = [t for t in tools if t.name != "execute_command"]

    wrapped_execute_command = add_human_in_the_loop(execute_command_tool)
    wrapped_search = add_human_in_the_loop(search)

    tools = other_tools + [wrapped_execute_command, wrapped_search]
    logger.info({"event": "tools_fetched", "tools": [t.name for t in tools]})

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

    logger.success({"event": "agent_created"})
    return agent

# ---- Main ----
if __name__ == "__main__":
    import asyncio

    async def main():
        agent = await init_executor()
        config = RunnableConfig({
            "recursion_limit": 15,
            "thread_id": str(uuid.uuid4()),  # type: ignore
        })
        
        response = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        # content="List all MCP tools you can use."
                        content="Try to execute 'ls -la /home/baolam' and then explain each file (use **execute_command** tool)"
                        # content="What process consumes most RAM and CPU on my computer?"
                    )
                ]
            },
            config=config,
            # stream_mode="debug"
        )

        try:
            interrupt = response.get("__interrupt__")[0]
            
            if interrupt:
                print("=" * 50)
                print("🚨 INTERRUPT")
                print("- Description:", interrupt.value.get("description"))

                args = interrupt.value.get("action_request", {})
                if args:
                    print("- Action Request:")
                    for k, v in args.items():
                        print(f"    • {k}: {v}")

                print("=" * 50)

                hil_result = input("👉 Allow action? (y/n): ").strip().lower()

                response = await agent.ainvoke(
                    Command(resume={"type": hil_result}),
                    config=config,
                    # stream_mode="debug"
                )
        except Exception as e:
            logger.error(e)

        logger.info({
            "event": "agent_response",
            "response": response['messages'][-1].content
        })
        print("Agent response:", response["messages"][-1].content)
        
    asyncio.run(main())
