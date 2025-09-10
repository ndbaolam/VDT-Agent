# workflow.py
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from loguru import logger
from planner import init_planner
from replanner import init_replanner, Response
from executor import init_executor
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from IPython.display import Image, display
import asyncio
import uuid

# ----------------------------
# State definition
# ----------------------------
class State(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

# ----------------------------
# Agents container
# ----------------------------
class Agents:
    executor = None
    planner = None
    replanner = None

    @classmethod
    async def init(cls, model: str = "gpt-4o-mini"):
        """
        Initialize all agents with given model.
        """
        cls.executor = await init_executor(model, temperature=0)
        cls.planner = await init_planner(model)
        cls.replanner = await init_replanner(model)

# ----------------------------
# Workflow step implementations
# ----------------------------
async def plan_step(state: State):
    response = await Agents.planner.ainvoke(
        {"messages": [HumanMessage(content=state["input"])]},
        # stream_mode="debug"
    )
    return {"plan": response.steps}

async def execute_step(state: State):
    plan = state.get("plan", [])
    if not plan:
        return {"past_steps": []}

    task = plan[0]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task_formatted = (
        f"For the following plan:\n{plan_str}\n\n"
        f"You are tasked with executing step 1: {task}."
    )

    response = await Agents.executor.ainvoke(
        {"messages": [HumanMessage(content=task_formatted)]},
        # stream_mode="debug"
    )

    return {"past_steps": [(task, response["messages"][-1].content)]}

async def replan_step(state: State):
    response = await Agents.replanner.ainvoke(
        state,
        # stream_mode="debug"
    )
    if isinstance(response.action, Response):
        return {"response": response.action.response}
    else:
        return {"plan": response.action.steps}

def should_end(state: State):
    return END if state.get("response") else "executor"

# ----------------------------
# Workflow graph
# ----------------------------
graph = (
    StateGraph(State)
    .add_node("planner", plan_step)
    .add_node("executor", execute_step)
    .add_node("replanner", replan_step)

    .add_edge(START, "planner")
    .add_edge("planner", "executor")
    .add_edge("executor", "replanner")

    .add_conditional_edges("replanner", should_end, ["executor", END])
    .compile(
        checkpointer=InMemorySaver()
    )
)

# ----------------------------
# Main execution
# ----------------------------
async def main():
    display(Image(graph.get_graph().draw_mermaid_png()))

    await Agents.init()

    thread_id = str(uuid.uuid4())

    config: RunnableConfig = {
        "recursion_limit": 10,
        "thread_id": thread_id,
    }
    inputs = {
        "input": "Try to execute 'ls -la' on my home folder and explain each files."
    }

    logger.info("🚀 Starting graph execution with initial input...")
    async for event in graph.astream(        
        inputs, 
        config=config,
        stream_mode="debug"
    ):
        for k, v in event.items():
            if k != "__end__":
                logger.debug(f"[Graph Event] {k}: {v}")

    logger.info("✅ First graph execution finished, resuming with Command(resume)...")
    async for event in graph.astream(        
        Command(resume={"type": "y"}),
        config=config,
        stream_mode="debug"
    ):
        for k, v in event.items():
            if k != "__end__":
                logger.debug(f"[Graph Resume Event] {k}: {v}")

    logger.success("🎉 Graph execution completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
