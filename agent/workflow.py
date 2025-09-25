import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import HumanMessage, AnyMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from langgraph.graph import add_messages
import uuid
from langgraph_supervisor import create_supervisor
from agent.executor import init_executor, ExecutorResponse
from agent.summarizer import init_summarizer
from agent.searcher import init_searcher, SearchResponse

from utils.pretty_print import pretty_print_messages

# ---- State ----
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    summarized_messages: list[AnyMessage]
    search_response: SearchResponse | None
    execution_response: ExecutorResponse | None

async def build_graph(model: str = "openai:gpt-4o-mini"):
    """Initialize all agents with the specified model"""
    llm = init_chat_model(model=model, temperature=0)
    
    executor = await init_executor(model=llm)
    searcher = init_searcher(model=llm)
    summarizer = init_summarizer(model=llm)
    
    supervisor = create_supervisor(
        model=llm,
        agents=[searcher, executor],
        pre_model_hook=summarizer,
        prompt=(
            "You are a supervisor, developed by VTNet (Viettel Network), managing 3 agents:\n"
            "- A search agent. Assign search-related tasks to this agent\n"
            "- An execution agent. Assign execution-related tasks like running commands, checking system status to this agent\n"
            "- A general LLM agent. Assign general language model tasks to this agent\n"
            "Assign work to one agent at a time, do not call agents in parallel.\n"
            "Do not do any work yourself."
        ),
        add_handoff_back_messages=True,
        output_mode="full_history",
    ).compile(
        name="GraphSupervisor",
        checkpointer=InMemorySaver(),
    )

    return supervisor

async def main():
    from utils.gen_image import save_graph_visualization
    graph = await build_graph()

    save_graph_visualization(graph)
    
    thread_id = str(uuid.uuid4())

    config = {
        "recursion_limit": 10,
        "thread_id": thread_id,
    }

    async for chunk in graph.astream(
        {"messages": [HumanMessage(content="Hello, who are you?")]},
        # stream_mode="messages",
        config=config,
    ):               
        pretty_print_messages(chunk)      
    


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())