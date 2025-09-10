from typing import Callable
from loguru import logger
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review."""
    if not isinstance(tool, BaseTool):
        logger.debug(f"Wrapping raw function '{tool.__name__}' into a BaseTool...")
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_ignore": True,   # = Reject/skip
            "allow_accept": True,   # = Approve
            "allow_edit": False,
            "allow_respond": False,
        }
        logger.debug("Using default interrupt_config.")

    @create_tool(
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    async def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        logger.info(f"🔔 Human-in-the-loop requested for tool: {tool.name}")
        logger.debug(f"Tool input: {tool_input}")

        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": "Please review the tool call"
        }
        response = interrupt(request)
        logger.debug(f"Human response: {response}")

        if response["type"] == "y":
            logger.info(f"✅ Approved: executing tool '{tool.name}'...")
            tool_response = await tool.ainvoke(tool_input, config)
            logger.success(f"Tool '{tool.name}' execution completed.")
        else:
            logger.error(f"❌ Unsupported interrupt response type: {response['type']}")
            raise ValueError(f"Unsupported interrupt response type: {response['type']}")

        return tool_response

    return call_tool_with_interrupt
