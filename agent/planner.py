from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from loguru import logger


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
For the given objective, come up with a simple step by step plan. 
This plan should involve individual tasks, that if executed correctly will yield the correct answer. 
Do not add any superfluous steps. 
The result of the final step should be the final answer. 
Make sure that each step has all the information needed - do not skip steps.
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
