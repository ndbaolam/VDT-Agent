import asyncio
from loguru import logger
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
import uuid

load_dotenv()

class VDTAgent:
    """
    A wrapper class for creating and managing a LangChain agent connected
    to one or more MCP servers.

    Attributes:
        llm (ChatOpenAI): The language model instance used by the agent.
        agent: The LangChain agent instance, initialized after tools are loaded.
        client (MultiServerMCPClient): The MCP client to interact with external tools.
    """

    def __init__(self, llm_model: str, **kwargs):
        """
        Initialize the Agent with a specified LLM model.

        Args:
            llm_model (str): The model name to use for ChatOpenAI.
            **kwargs: Additional keyword arguments to pass to ChatOpenAI.
        """
        logger.info(f"Initializing Agent with model: {llm_model}")
        self.llm = ChatOpenAI(model=llm_model, **kwargs)
        self.agent = None
        self.memory = MemorySaver()
        self.client = MultiServerMCPClient(
            {
                "system-metrics-mcp": {
                    "command": "python",
                    "args": ["mcp/server.py"],
                    "transport": "stdio",
                }
            }
        )

    async def set_agent(self) -> None:
        """
        Fetch tools from the MCP client and create the LangChain agent.

        This method should be called before running any queries with the agent.
        """
        logger.info("Fetching tools from MCP client...")
        tools = await self.client.get_tools()
        logger.info(f"Fetched {len(tools)} tools: {[t.name for t in tools]}")
        
        self.agent = create_react_agent(
            model=self.llm,
            tools=tools,
            checkpointer=self.memory,
            # debug=True,
        )
        logger.success("Agent created successfully.")

    async def run(self, messages, config: RunnableConfig | None = None) -> (dict[str, Any] | Any):
        """
        Run the agent asynchronously with a given input query.
        """
        if self.agent is None:
            logger.warning("Agent is not initialized. Call set_agent() first.")
            return None
        logger.info(f"Running agent with query: {messages}")
        try:            
            result = await self.agent.ainvoke(
                { "messages": messages },
                config=config,
                stream_mode="values"
            )
            logger.success(f"Agent result: {result}")
            return result
        except Exception as e:
            logger.exception(f"Error running agent: {e}")
            return None    

async def main():
    """
    Example usage of the Agent class.

    Creates an agent, sets it up with tools from MCP, runs a sample query,
    and prints the result.
    """
    agent = VDTAgent("gpt-4o-mini", temperature=0)
    
    await agent.set_agent()
        
    messages = [
        SystemMessage(
            content="You are a helpful assistant."
        ),
        HumanMessage(
            content="There is a process, which PID is 264730, can you help me to get its metrics and after that kill it."
        )
    ]
    
    config = RunnableConfig(
        recursion_limit=10,
        configurable={
            "thread_id": str(uuid.uuid4())
        }
    )
    
    result = await agent.run(messages, config)    
        
    for step in result["messages"]:
        logger.info(f"{step.pretty_print()}")
        
if __name__ == "__main__":
    asyncio.run(main())
