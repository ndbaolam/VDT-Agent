import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import HumanMessage, AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from langgraph.graph import (
    StateGraph, 
    END, 
    START, 
    add_messages
)
import uuid
from agent.executor import init_executor
from agent.summarizer import init_summarizer

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

# ---- State ----
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    summarized_messages: list[AnyMessage]

# ---- Agents ----
class Agents:
    executor = None
    summarizer = None

    @classmethod
    async def init(cls, model: str = "openai:gpt-4o-mini"):
        logger.info(f"Initializing Agents with model={model}")
        llm = init_chat_model(model=model, temperature=0)
        cls.executor = await init_executor(model=llm)
        cls.summarizer = init_summarizer(model=llm.bind(max_token=1024))

async def execute_step(state: State):
    response = await Agents.executor.ainvoke(
        {
            "messages": state['summarized_messages']
        }
    )    
    return {"messages": response["messages"][-1]}

async def build_graph():
    await Agents.init()

    graph = (
        StateGraph(State)
        .add_node("executor", execute_step)
        .add_node("summarize", Agents.summarizer)
        .add_edge(START, "summarize")
        .add_edge("summarize", "executor")
        .add_edge("executor", END)
        .compile(
            checkpointer=InMemorySaver()
        )
    )

    return graph

# ---- Main ----
async def main():
    graph = await build_graph()

    thread_id = str(uuid.uuid4())

    config: RunnableConfig = {
        "recursion_limit": 10,
        "thread_id": thread_id,
    }

    async for chunk in graph.astream(
        {"messages": [HumanMessage(content="Show me my system metrics")]},
        # stream_mode="messages",
        config=config,
    ):
        if "__interrupt__" in chunk:
            interrupts = chunk.get("__interrupt__") or []
            interrupt = interrupts[0] if interrupts else None
            if interrupt:
                print("🚨 INTERRUPT")
                print("- Description:", interrupt.value.get("description"))
                args = interrupt.value.get("action_request", {})
                if args:
                    print("- Action Request:")
                    for k, v in args.items():
                        print(f"  • {k}: {v}")
                print("=" * 50)
                hil_result = input("👉 Allow action? (y/n): ").strip().lower()
                
                async for message_chunk, metadata in graph.astream(
                    Command(resume={"type": hil_result}),
                    stream_mode="messages",
                    config=config,
                ):
                    if message_chunk.content:
                        print(message_chunk.content, end="\n", flush=True)       
        else:
            for node_name, node_data in chunk.items():
                if "messages" in node_data:
                    print(node_data['messages'].content)
                    # for message in node_data["messages"]:                        
                    #     print(message[1], end="", flush=True)         

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
