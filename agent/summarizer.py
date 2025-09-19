import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.language_models import BaseChatModel

def init_summarizer(model: BaseChatModel):
    """Create and configure the summarization node."""
    return SummarizationNode(
        token_counter=count_tokens_approximately,
        model=model,
        max_tokens=1024,
        max_tokens_before_summary=1024,
        max_summary_tokens=256,
    )
