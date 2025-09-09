from typing import Union
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger
from planner import Plan


class Response(BaseModel):
    """Represents a direct response to the user."""
    response: str


class Act(BaseModel):
    """
    Represents an action the agent can take.
    
    Attributes:
        action (Union[Response, Plan]): Either respond to the user directly,
        or produce an updated plan with remaining steps.
    """
    action: Union[Response, Plan] = Field(
        description="If you want to respond to the user, use Response. "
        "If more steps are needed, return a Plan with only the remaining steps."
    )


async def init_replanner(model_name: str = "gpt-4o"):
    """
    Initialize the RePlanner with a ChatOpenAI model and a predefined prompt.

    Args:
        model_name (str): The model name to use. Defaults to "gpt-4o".

    Returns:
        llm: A LangChain pipeline object with structured output (Act).
    """
    logger.info(f"Initializing RePlanner with model: {model_name}")

    # Prompt template
    prompt = ChatPromptTemplate.from_messages(
        ["""For the given objective, come up with a simple step by step plan. 
This plan should involve individual tasks, that if executed correctly will yield the correct answer. 
Do not add any superfluous steps. 
The result of the final step should be the final answer. 
Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the following steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can respond to the user, then use Response. 
Otherwise, return a Plan with only the steps that still NEED to be done. 
Do not repeat already completed steps.
"""]
    )

    # LLM with structured output
    llm = prompt | ChatOpenAI(
        model=model_name,
        temperature=0,
    ).with_structured_output(Act)

    logger.success("RePlanner initialized successfully.")
    return llm