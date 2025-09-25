import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from tools.interruptor import add_human_in_the_loop
from tools.retriever import get_retriever_tool
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

class SearchResponse(BaseModel):
    description: str = Field(..., description="Description of the issue.")
    solutions: List[str] = Field(..., description="List of possible solutions.")
    confidence: float = Field(..., description="Confidence score between 0 and 1.")

def init_tools():
    tools = []

    # Add DuckDuckGo Search Tool
    search_tool = DuckDuckGoSearchRun()
    search_tool = add_human_in_the_loop(search_tool)
    tools.append(search_tool)
    # Add Retriever Tool
    retriever_tool = get_retriever_tool()
    tools.append(retriever_tool)    
    
    return tools

def init_searcher(model: BaseChatModel):        
    tools = init_tools()
    
    prompt = ("""
Your role is to find possible solutions for user-reported issues.

Rules:
1. Always search the Known Error Database (KEDB) first.
2. If no relevant solutions are found in KEDB, then use external tools 
   (e.g., search engines, documentation retrievers).
3. Include confidence score and source (KEDB / external).
""")

    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=prompt,
        response_format=SearchResponse,
        name="searcher",
    )

    logger.info(f"Executor initialized with model={model.get_name()}")
    return agent

if __name__ == "__main__":
    import asyncio
    from langchain.chat_models import init_chat_model

    async def main():
        model = init_chat_model("openai:gpt-4.1-mini")
        searcher = init_searcher(model)
        response = searcher.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "Kubernetes pod eviction"
                }
            ]
        })

        print(response["structured_response"])

    
    asyncio.run(main())
