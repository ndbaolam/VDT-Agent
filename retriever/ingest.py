import os
import json
from loguru import logger
from connect import VectorDB

logger.add("rag/ingest.log", rotation="10 MB", retention="7 days", level="DEBUG")

def ingest():
    logger.info("Starting ingestion process...")
        
    db = VectorDB(        
        config_file="config.yaml"
    )

    collection_name = "kedb_collection"

    try:
        logger.info("Connecting to Milvus collection '{}'", collection_name)
        db.connect(collection_name)

        # Load data
        logger.info("Loading KEDB data from 'kedb-mock.json'")
        with open("kedb-mock.json", "r", encoding="utf-8") as f:
            kedb_data = json.load(f)

        logger.info("Loaded {} records from JSON", len(kedb_data))

        # Ingest data
        logger.info("Starting data ingestion into Milvus...")
        db.ingest(kedb_data, collection_name)

        # Create index
        logger.info("Creating index for collection '{}'", collection_name)
        db.create_index(collection_name)

    except Exception as e:
        logger.exception("An error occurred during ingestion: {}", e)
    finally:
        db.disconnect()
        logger.info("Ingestion process finished")


if __name__ == "__main__":
    ingest()