import click
from connect import VectorDB
from loguru import logger


@click.command()
@click.option("--text", "-t", required=True, help="Text to search in the KEDB")
@click.option("--collection", "-c", default=None, help="Milvus collection name")
@click.option("--top-k", "-k", default=3, help="Number of top results to return")
def query_cli(text, collection, top_k):
    logger.info("Starting query CLI")

    db = VectorDB()

    try:
        logger.info("Connecting to Milvus collection '{}'", collection or db.default_collection_name)
        db.connect(collection)

        logger.info("Querying text: '{}' | top_k={}", text[:50], top_k)
        results = db.query(text=text, top_k=top_k)

        click.echo(f"\n🔍 Query: {text}\n")
        for i, doc in enumerate(results, 1):
            meta = doc.metadata
            click.echo(f"{i}. {meta.get('title')}")
            click.echo(f"   Description: {meta.get('description')}")
            click.echo(f"   Solution: {meta.get('solution')}")
            click.echo(f"   Root Cause: {meta.get('root_cause')}\n")

        logger.success("Query completed successfully, returned {} results", len(results))
    except Exception as e:
        logger.exception("An error occurred during query: {}", e)
    finally:
        logger.info("Query CLI finished")


if __name__ == "__main__":
    query_cli()
