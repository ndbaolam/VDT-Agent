import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from loguru import logger
from tools.handoff import create_handoff_tool
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

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


# Handoffs
assign_to_executor_agent = create_handoff_tool(
    agent_name="executor",
    description="Assign task to a systemic agent.",
)

assign_to_translator_agent = create_handoff_tool(
    agent_name="translator",
    description="Assign task to a translator agent.",
)

def init_supervisor(model: BaseChatModel):        
    supervisor_agent = create_react_agent(
        model=model,
        tools=[assign_to_executor_agent, assign_to_translator_agent],
        prompt = (
                "You are a supervisor managing two agents:\n"
                "- Executor agent: handles system-related tasks, always works in English.\n"
                "- Translator agent: translates between Vietnamese and English.\n\n"
                "## Rules\n"
                "1. When the user input is in Vietnamese:\n"
                "   - First, use the translator agent to translate it into English.\n"
                "   - Then send the English text to the executor agent.\n\n"
                "2. When the user input is in English:\n"
                "   - Send it directly to the executor agent (no translation needed).\n"
                "   - If the executor output needs to be shown to the user, return it as is (in English).\n\n"
                "3. Assign work to only one agent at a time. Do not execute tasks yourself.\n"                
            ),
        name="supervisor",
    )

    return supervisor_agent
