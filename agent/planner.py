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
For each objective, you must come up with a simple, precise plan. 
Each step should be actionable and contain all information required to produce the correct final answer. 
Do not include unnecessary steps.

You have access to the following tools:

1. get_system_metrics(metrics_type="all")
2. get_process_metrics(pid=None)
3. execute_command(command: str, cwd: Optional[str]=None, timeoutSec: int=30)
4. query_kedb(text: str, collection: str, top_k: int=3)

Guidelines for planning and execution:
- Always consider which tool is best suited for each step.
- Provide clear instructions for using each tool.
- The last step in the plan must produce the final answer.
- Ensure all required context for executing a step is included.
- Avoid skipping any intermediate steps or assumptions.
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
