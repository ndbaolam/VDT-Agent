import uuid
from loguru import logger
from agent.workflow import graph, Agents
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

async def init_agents():
    logger.info("🚀 Initializing Agents...")
    await Agents.init()
    logger.info("✅ Agents initialized successfully.")

async def process_chat(input_text: str):
    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {
        "recursion_limit": 40,
        "thread_id": thread_id,
    }

    inputs = {"input": input_text}

    response = await graph.ainvoke(inputs, config=config, stream_mode="values")

    # Handle interrupt
    interrupt_data = None
    interrupts = response.get("__interrupt__") or []
    if interrupts:
        interrupt = interrupts[0]
        interrupt_data = {
            "description": interrupt.value.get("description", "No description"),
            "action_request": interrupt.value.get("action_request") or {},
        }

    # Extract last step
    past_steps = response.get("past_steps") or []

    if past_steps:
        last_step = past_steps[-1]
        if isinstance(last_step, (list, tuple)) and len(last_step) >= 2:
            _, result = last_step
        else:
            result = str(last_step)
    else:
        result = "Something went wrong! Please try again."

    return thread_id, result, interrupt_data


async def resume_chat(thread_id: str, decision: str):
    config: RunnableConfig = {
        "recursion_limit": 40,
        "thread_id": thread_id,
    }

    response = await graph.ainvoke(
        Command(resume={"type": decision}),
        config=config,
        stream_mode="values",
    )

    past_steps = response.get("past_steps") or []

    if past_steps:
        last_step = past_steps[-1]
        if isinstance(last_step, (list, tuple)) and len(last_step) >= 2:
            _, result = last_step
        else:
            result = str(last_step)
    else:
        result = "Something went wrong! Please try again."

    return result
