from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langchain_milvus import Milvus
from langchain_core.documents import Document
from loguru import logger
from dotenv import load_dotenv
import os
import sys

load_dotenv()

# ---- Logging config ----
LOG_DIR = os.path.join(os.path.dirname(__file__), "../..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "all.log")

logger.remove()
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

# ---- Env config ----
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", 19530)
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "kedb_collection")


class VectorDB:
    def __init__(self):
        self.host = MILVUS_HOST
        self.port = MILVUS_PORT
        self.default_collection_name = COLLECTION_NAME

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise RuntimeError("OPENAI_API_KEY not found")

        # Embeddings
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
        )

        self.vectorstore: Optional[Milvus] = None

        logger.info(
            "VectorDB initialized with host={}, port={}, default_collection={}", 
            self.host, self.port, self.default_collection_name
        )

    def connect(self, collection_name: Optional[str] = None):
        if not collection_name:
            collection_name = self.default_collection_name

        try:
            self.vectorstore = Milvus(
                embedding_function=self.embedding_model,
                connection_args={"host": self.host, "port": self.port},
                collection_name=collection_name,
                drop_old=False,
                auto_id=True
            )
            logger.info(
                "Connected to Milvus at {}:{} with collection '{}'", 
                self.host, self.port, collection_name
            )
        except Exception as e:
            logger.exception("Failed to connect to Milvus: {}", e)
            raise

    def ingest(self, kedb_data: List[Dict[str, Any]]):
        if not self.vectorstore:
            logger.error("Vectorstore not initialized. Call connect() first.")
            raise RuntimeError("Vectorstore not initialized. Call connect() first.")

        docs = []
        for idx, entry in enumerate(kedb_data, start=1):
            content = f"{entry.get('title', '')}\n{entry.get('description', '')}"
            metadata = {
                "title": entry.get("title", ""),
                "description": entry.get("description", ""),
                "root_cause": entry.get("root_cause", ""),
                "solution": entry.get("solution", "")
            }
            docs.append(Document(page_content=content, metadata=metadata))
            logger.debug("Prepared entry {} -> title='{}'", idx, entry.get("title", ""))

        try:
            self.vectorstore.add_documents(docs)
            logger.success(
                "Inserted {} records into '{}'", len(docs), self.default_collection_name
            )
        except Exception as e:
            logger.exception("Failed to insert documents: {}", e)

    def query(self, text: str, top_k: int = 3):
        if not self.vectorstore:
            logger.error("Vectorstore not initialized. Call connect() first.")
            raise RuntimeError("Vectorstore not initialized. Call connect() first.")

        try:
            results = self.vectorstore.similarity_search(text, k=top_k)
            logger.info(
                "Query executed on '{}': top_k={}", self.default_collection_name, top_k
            )
            return results
        except Exception as e:
            logger.exception(
                "Failed to query collection '{}': {}", self.default_collection_name, e
            )
            raise
