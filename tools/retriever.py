import os, sys
from loguru import logger
from langchain.tools.retriever import create_retriever_tool
from .rag.connect import VectorDB
from dotenv import load_dotenv

load_dotenv()

def get_retriever_tool():
    db = VectorDB()
    collection_name = os.getenv("COLLECTION_NAME")

    try:
        db.connect(collection_name)

        retriever = db.vectorstore.as_retriever()

        retriever_tool = create_retriever_tool(
            retriever,
            "query_kedb",
            "Search in KEDB (Known Errors Database) and return information.",
        )

        return retriever_tool
    except Exception as e:
        logger.error(f"Connection Error: {e}")