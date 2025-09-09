from loguru import logger
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.client import MultiServerMCPClient

async def init_agent(llm_model: str = "gpt-4o-mini", **kwargs):    
    logger.info(f"Initializing agent with model: {llm_model}")
    llm = ChatOpenAI(model=llm_model, **kwargs)
    
    client = MultiServerMCPClient(
        {
            "system-metrics-mcp": {
                "command": "python",
                "args": ["server.py"],
                "transport": "stdio",
            }
        }
    )
    tools = await client.get_tools()
    logger.info(f"Fetched {len(tools)} tools: {[t.name for t in tools]}")
    
    memory = MemorySaver()
    agent = create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        prompt="""
        You are a helpful assistant that uses the following tools to answer user queries.
        Make sure to use the tools when needed, and provide clear and concise answers.
        """,
    )

    logger.success("Agent created successfully.")
    return agent
