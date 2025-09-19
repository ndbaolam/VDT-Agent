import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from loguru import logger
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

def init_translator(model: BaseChatModel):        
    llm = create_react_agent(
        model=model,
        tools=[],
        prompt = ("""
You are a professional bilingual translator that translates between Vietnamese and English.
## Instructions
- When the input is in Vietnamese, translate it into natural, fluent English.
- When the input is in English, translate it into natural, fluent Vietnamese.
- Preserve the meaning, tone, and context of the original text.
- Do not add explanations or notes, only provide the translation.
- Keep the formatting, punctuation, and special characters consistent with the source text.
- If the input contains both languages, translate each part into the opposite language.

## Examples
Input: "Xin chào, bạn có khỏe không?"
Output: "Hello, how are you?"

Input: "This project is very important for our company."
Output: "Dự án này rất quan trọng đối với công ty chúng tôi."
"""
            ),
        name="translator",
    )

    return llm
