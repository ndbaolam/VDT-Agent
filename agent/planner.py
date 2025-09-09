from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from dotenv import load_dotenv
import os

load_dotenv()

class Plan(BaseModel):
    """Represents a step-by-step plan for a given objective."""
    steps: List[str] = Field(
        description="Individual ordered steps required to achieve the final result"
    )


async def init_planner(model_name: str = "gpt-4o"):
    """
    Initialize a Planner with a ChatOpenAI model and predefined prompt.

    Args:
        model_name (str): The name of the model to use. Defaults to "gpt-4o".

    Returns:
        llm: A LangChain pipeline object that can be invoked with structured output (Plan).
    """
    logger.info(f"Initializing Planner with model: {model_name}")

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
   - Collects system metrics.
   - metrics_type can be: "system", "cpu", "ram", "disk", or "all".
   - Returns a dictionary or list of dictionaries with system, CPU, RAM, and disk information.

2. get_process_metrics(pid=None)
   - Collects metrics of running processes.
   - If pid is provided, returns metrics only for that process.
   - If pid is None, returns top 10 processes by memory usage.
   - Returns a dictionary including pid, name, user, status, CPU percent, memory percent.

3. execute_command(command: str, cwd: Optional[str]=None, timeoutSec: int=30)
   - Executes a system command safely without using the shell.
   - Returns structured text including stdout, stderr, return code, or error messages.

4. query_kedb(text: str, collection: str, top_k: int=3)
   - Queries the RAG knowledge base (Milvus) for known errors.
   - Returns a list of relevant entries with fields: id, title, description, solution, root_cause, score.

Guidelines for planning and execution:

- Always consider which tool is best suited for each step.
- Provide clear instructions for using each tool, including parameters if needed.
- The last step in the plan must produce the final answer.
- Ensure that all required context for executing a step is included.
- Avoid skipping any intermediate steps or assumptions.
"""),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    # LLM with structured output
    llm = prompt | ChatOpenAI(
        model=model_name,
        temperature=0,
    ).with_structured_output(Plan)

    logger.success("Planner initialized successfully.")
    return llm

if __name__ == "__main__":
    import asyncio

    async def main():
        planner = await init_planner()
        response = await planner.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content="How to deal with high memory usage on my computer? Don't run any shell commands."
                    )
                ]
            }
        )
        print("Planner response:", response.steps)
    
    asyncio.run(main())