import os
import json
from loguru import logger
from connect import VectorDB 

def ingest():
    logger.info("Starting ingestion process...")
        
    db = VectorDB()

    collection_name = os.getenv("COLLECTION_NAME")

    try:
        logger.info("Connecting to Milvus collection '{}'", collection_name)
        db.connect(collection_name)

        # Load data
        data_path = "retriever/kedb-mock.json"
        logger.info("Loading KEDB data from '{}'", data_path)

        with open(data_path, "r", encoding="utf-8") as f:
            kedb_data = json.load(f)

        logger.info("Loaded {} records from JSON", len(kedb_data))

        # Ingest data
        logger.info("Starting data ingestion into Milvus...")
        db.ingest(kedb_data)

    except Exception as e:
        logger.exception("An error occurred during ingestion: {}", e)
    finally:
        logger.info("Ingestion process finished")


if __name__ == "__main__":
    ingest()
