# workflow.py
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from loguru import logger
from agent.planner import init_planner
from agent.replanner import init_replanner, Response
from agent.executor import init_executor
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
import asyncio
import uuid
import os
import json

# ---- Logging setup JSON ----
ENABLE_LOGGING = os.getenv("WORKFLOW_LOGGING", "1") == "1"
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

if ENABLE_LOGGING:
    logger.remove()
    logger.add(
        f"{log_folder}/workflow.json",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        enqueue=True,
        serialize=True,  # <-- JSON logging
        backtrace=True,
        diagnose=True,
    )
else:
    logger.remove()

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
        logger.info({"event": "agents_init_start", "model": model})
        cls.executor = await init_executor(model, temperature=0)
        cls.planner = await init_planner(model)
        cls.replanner = await init_replanner(model)
        logger.success({"event": "agents_init_completed"})

# ----------------------------
# Workflow step implementations
# ----------------------------
def classification(state: State):
    input = state['input']
    

async def plan_step(state: State):
    response = await Agents.planner.ainvoke(
        {"messages": [HumanMessage(content=state["input"])]}
    )
    logger.info({"event": "plan_step_completed", "plan": response.steps})
    return {"plan": response.steps}

async def execute_step(state: State):
    plan = state.get("plan", [])
    if not plan:
        return {"past_steps": []}

    task = plan[0]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task_formatted = f"For the following plan:\n{plan_str}\n\nYou are tasked with executing step 1: {task}."

    response = await Agents.executor.ainvoke(
        {
            "messages": [HumanMessage(content=task_formatted)]
        },
    )
    past_step = (task, response['messages'][-1].content)
    logger.info({"event": "execute_step_completed", "past_step": past_step})
    return {"past_steps": [past_step]}

async def replan_step(state: State):
    response = await Agents.replanner.ainvoke(
        state,
        stream_mode="debug"
    )
    if isinstance(response.action, Response):
        logger.info({"event": "replan_step_completed", "response": response.action.response})
        return {"response": response.action.response}
    else:
        logger.info({"event": "replan_step_updated_plan", "plan": response.action.steps})
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
    await Agents.init()

    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {
        "recursion_limit": 10,
        "thread_id": thread_id,
    }
    # inputs = {"input": "Try to execute 'ls -la' on my home folder and explain each files."}
    inputs = {"input": "Hello."}

    logger.info({"event": "graph_execution_start", "input": inputs})

    # async for event in graph.astream(inputs, config=config, stream_mode="debug"):
    #     print(30 * "-")
    #     print(json.dumps(event, indent=4)) 

    # print(15 * "***" + "graph_execution_resume_start" + 15 * "***")
    # logger.info({"event": "graph_execution_resume_start"})
    # print(graph.get_graph(config=config))
    # async for event in graph.astream(Command(resume={"type": "y"}), config=config, stream_mode="debug"):
    #     print(30 * "-")
    #     print(json.dumps(event, indent=4)) 

    response = await graph.ainvoke(inputs, config=config, stream_mode="values")

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
                stream_mode="values"
            )
    except Exception as e:
        logger.error(e)

    print("\n" + "=" * 50)
    print("🤖 Agent Response")
    print("=" * 50)
    print(response.get("response", "No response"))

    steps = response.get("past_steps", [])
    if steps:
        print("\n" + "=" * 50)
        print("📜 Execution Steps")
        print("=" * 50)
        for i, step in enumerate(steps, 1):
            action, result = step  # unpack tuple
            print(f"👉 Action : {action}")
            print(f"✅ Result :\n{result}")

    print("\n" + "=" * 50)
    print("✅ Graph execution completed")
    print("=" * 50)

    logger.success({"event": "graph_execution_completed"})

if __name__ == "__main__":
    asyncio.run(main())
