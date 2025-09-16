import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage
from langchain_core.caches import InMemoryCache
from langgraph.checkpoint.memory import InMemorySaver
from tools import init_tools
from dotenv import load_dotenv
import uuid

load_dotenv()

ENABLE_LOGGING = os.getenv("WORKFLOW_LOGGING", "1") == "1"

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
