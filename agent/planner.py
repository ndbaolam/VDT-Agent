import sys
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv
from loguru import logger
import os

load_dotenv()

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


# ---- Planner schema ----
class Plan(BaseModel):
    """Represents a step-by-step plan for a given objective."""
    steps: List[str] = Field(
        description="Individual ordered steps required to achieve the final result"
    )


# ---- Planner init ----
async def init_planner(model: BaseChatModel):
    """
    Initialize a Planner with a ChatOpenAI model and predefined prompt.
    """

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

    llm = prompt | model.with_structured_output(Plan)

    logger.info(f"Planner initialized with model={model.get_name()}")
    return llm
