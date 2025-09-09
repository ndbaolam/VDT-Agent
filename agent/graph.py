# workflow.py
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from planner import init_planner
from replanner import init_replanner, Response
from executor import init_executor
from langchain_core.messages import HumanMessage
import asyncio

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
        {"messages": [HumanMessage(content=task_formatted)]}
    )

    return {"past_steps": [(task, response["messages"][-1].content)]}


async def plan_step(state: State):
    response = await Agents.planner.ainvoke(
        {"messages": [HumanMessage(content=state["input"])]}
    )
    return {"plan": response.steps}


async def replan_step(state: State):
    response = await Agents.replanner.ainvoke(state)
    if isinstance(response.action, Response):
        return {"response": response.action.response}
    else:
        return {"plan": response.action.steps}


def should_end(state: State):
    return END if state.get("response") else "agent"

# ----------------------------
# Workflow graph
# ----------------------------
workflow = StateGraph(State)

workflow.add_node("planner", plan_step)
workflow.add_node("agent", execute_step)
workflow.add_node("replan", replan_step)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", "replan")

workflow.add_conditional_edges("replan", should_end, ["agent", END])

app = workflow.compile()

# ----------------------------
# Main execution
# ----------------------------
async def main():
    await Agents.init()
    config = {"recursion_limit": 5}
    inputs = {
        "input": "How to deal with high memory usage on my computer? Don't run any shell commands."
    }
    async for event in app.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                print(v)

if __name__ == "__main__":
    asyncio.run(main())
