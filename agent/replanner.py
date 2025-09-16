import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from typing import Union
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from agent.planner import Plan
from dotenv import load_dotenv

load_dotenv()

class Response(BaseModel):
    """Represents a direct response to the user."""
    response: str


class Act(BaseModel):
    """
    Represents an action the agent can take.
    Either respond to the user directly, or produce an updated plan.
    """
    action: Union[Response, Plan] = Field(
        description="If responding to the user, use Response. Otherwise, return a Plan with remaining steps."
    )


async def init_replanner(model_name: str = "gpt-4o"):
    prompt = ChatPromptTemplate.from_messages(
        ["""For the given objective, come up with a simple step by step plan. 
This plan should involve individual tasks that yield the correct answer. 
Do not add any superfluous steps. 

Your objective was this:
{summarized_messages}

Your original plan was this:
{plan}

You have currently done the following steps:
{past_steps}

Update your plan accordingly. If no more steps are needed, use Response. 
Otherwise, return a Plan with only the steps that still NEED to be done. 
Do not repeat already completed steps.
"""]
    )

    llm = prompt | init_chat_model(
        model=model_name,
        temperature=0,
    ).with_structured_output(Act)

    return llm