import click
from connect import VectorDB
import os
from loguru import logger

# logger.add("rag/query.log", rotation="10 MB", retention="7 days", level="DEBUG")

@click.command()
@click.option("--text", "-t", required=True)
@click.option("--collection", "-c", default=None)
@click.option("--top-k", "-k", default=3)
def query_cli(text, collection, top_k):
    logger.info("Starting query CLI")
        
    db = VectorDB()
    
    try:
        logger.info("Connecting to Milvus collection '{}'", collection or db.default_collection_name)
        db.connect(collection)

        logger.info("Querying text: '{}' | top_k={}", text[:50], top_k)
        results = db.query(text=text, top_k=top_k, collection_name=collection)

        click.echo(f"\n🔍 Query: {text}\n")
        for i, r in enumerate(results, 1):
            entity = r.entity
            click.echo(f"{i}. [Score: {r.score:.4f}] {entity.get('title')}")
            click.echo(f"   ID: {entity.get('id')}")
            click.echo(f"   Description: {entity.get('description')}")
            click.echo(f"   Solution: {entity.get('solution')}\n")
            click.echo(f"   Root Cause: {entity.get('root_cause')}\n")

        logger.success("Query completed successfully, returned {} results", len(results))
    except Exception as e:
        logger.exception("An error occurred during query: {}", e)
    finally:
        db.disconnect()
        logger.info("Disconnected from Milvus, query CLI finished")

if __name__ == "__main__":
    query_cli()
