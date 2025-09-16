from typing import Callable
from loguru import logger
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt
import os

# ---- Logging setup JSON ----
ENABLE_LOGGING = os.getenv("WORKFLOW_LOGGING", "1") == "1"
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)

if ENABLE_LOGGING:
    logger.remove()
    logger.add(
        f"{log_folder}/interruptor.json",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        enqueue=True,
        serialize=True,  # <-- JSON
        backtrace=True,
        diagnose=True,
    )
else:
    logger.remove()


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review with JSON logging."""
    if not isinstance(tool, BaseTool):
        logger.debug({"event": "wrap_function", "tool_name": tool.__name__})
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_ignore": True,
            "allow_accept": True,
            "allow_edit": False,
            "allow_respond": False,
        }
        logger.debug({"event": "default_interrupt_config", "tool": tool.name})

    @create_tool(
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    async def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        logger.info({
            "event": "human_in_loop_request",
            "tool": tool.name,
            "tool_input": tool_input
        })

        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": "Please review the tool call"
        }
        response = interrupt(request)
        logger.info({
            "event": "human_response",
            "tool": tool.name,
            "response": response
        })

        if response["type"] == "y":
            logger.info({"event": "tool_execute_start", "tool": tool.name})
            tool_response = await tool.ainvoke(tool_input, config)
            logger.success({
                "event": "tool_execute_completed",
                "tool": tool.name,
                "response": str(tool_response)
            })
        else:
            logger.error({
                "event": "tool_execute_rejected",
                "tool": tool.name,
                "response_type": response["type"]
            })
            raise ValueError(f"Unsupported interrupt response type: {response['type']}")

        return tool_response

    return call_tool_with_interrupt
