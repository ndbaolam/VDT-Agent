import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import HumanMessage, AnyMessage
from langmem.short_term import SummarizationNode
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langgraph.types import Command
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.graph import (
    StateGraph, 
    END, 
    START, 
    add_messages
)
import uuid
from agent.executor import init_executor

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    summarized_messages: list[AnyMessage]

class Agents:
    executor = None
    summarization_model = None

    @classmethod
    async def init(cls, model: str = "gpt-4o-mini"):
        cls.executor = await init_executor(model, temperature=0)
        cls.summarization_model = init_chat_model(f"openai:{model}").bind(max_tokens=128)

summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=Agents.summarization_model,
    max_tokens=1024,
    max_tokens_before_summary=1024,
    max_summary_tokens=256,
)

async def execute_step(state: State):
    response = await Agents.executor.ainvoke(
        {
            "messages": state['summarized_messages']
        }
    )    

    return {"messages": response["messages"][-1]}

graph = (
    StateGraph(State)
    .add_node("executor", execute_step)
    .add_node("summarize", summarization_node)

    .add_edge(START, "summarize")
    .add_edge("summarize", "executor")
    .add_edge("executor", END)

    .compile(
        checkpointer=InMemorySaver()
    )
)

async def main():
    await Agents.init()

    thread_id = str(uuid.uuid4())

    config: RunnableConfig = {
        "recursion_limit": 10,
        "thread_id": thread_id,
    }

    response = await graph.ainvoke(
        {
           "messages": [HumanMessage(content="hola")]
        },
        config=config, 
        # stream_mode="values"
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

            response = await graph.ainvoke(
                Command(resume={"type": hil_result}),
                config=config,
                # stream_mode="values"
            )
    except Exception as e:
        print(e)

    print("\n" + "=" * 50)
    print("🤖 Agent Response")
    response["messages"][-1].pretty_print()

if __name__ == "__main__":
    import asyncio
    
    asyncio.run(main())