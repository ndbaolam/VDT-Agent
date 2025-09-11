from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from dotenv import load_dotenv
import os

# ---- Logging setup JSON ----
ENABLE_LOGGING = os.getenv("WORKFLOW_LOGGING", "1") == "1"
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

if ENABLE_LOGGING:
    logger.remove()
    logger.add(
        f"{log_folder}/planner.json",
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

load_dotenv()

class Plan(BaseModel):
    """Represents a step-by-step plan for a given objective."""
    steps: List[str] = Field(
        description="Individual ordered steps required to achieve the final result"
    )


async def init_planner(model_name: str = "gpt-4o"):
    """
    Initialize a Planner with a ChatOpenAI model and predefined prompt.
    """
    logger.info({"event": "init_planner_start", "model": model_name})

    # Prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content="""
You are an intelligent agent tasked with solving user objectives step by step. 

Guidelines:

1. Analyze the user question first:
   - If the question is simple, trivial, or conversational (e.g., "Hello", "How are you?", "What time is it?"), respond **directly** without creating a step-by-step plan.
   - Only create a plan if the question requires actionable steps or investigation to reach an answer.

2. For questions that need a plan, create the simplest actionable plan leading directly to the final answer:
   - Determine the minimum steps needed.
     - Simple questions may require only one step.
     - Complex questions can be broken down into multiple clear steps.
   - Each step must include:
     - **Goal** of the step.
     - **Tool to use**.
     - **All parameters needed** for execution.

3. Available tools:
   1. `get_system_metrics(metrics_type="all")`: Collect system metrics.
   2. `get_process_metrics(pid=None)`: Collect metrics of running processes including PID, name, user, status, CPU and memory usage.
   3. `execute_command(command: str, cwd: Optional[str]=None, timeoutSec: int=30)`: Execute a system command safely (without shell).
   4. `query_kedb(text: str, collection: str, top_k: int=3)`: Query the RAG knowledge base (Milvus) for relevant known errors.

4. Last step must produce the final answer.

5. Avoid unnecessary or redundant steps.

6. Format steps clearly and concisely.
"""),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    llm = prompt | ChatOpenAI(
        model=model_name,
        temperature=0,
    ).with_structured_output(Plan)

    logger.success({"event": "planner_initialized"})
    return llm


if __name__ == "__main__":
    import asyncio

    async def main():
        planner = await init_planner()
        user_input = "How to deal with high memory usage on my computer? Don't run any shell commands."
        logger.info({"event": "planner_invoke_start", "input": user_input})

        response = await planner.ainvoke(
            {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            }
        )

        logger.info({
            "event": "planner_invoke_completed",
            "steps": response.steps
        })
        print("Planner response:", response.steps)
    
    asyncio.run(main())
