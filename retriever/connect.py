import yaml
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection,  FieldSchema, CollectionSchema, DataType
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    def __init__(self, config_file: str = "rag/config.yaml"):
        with open(config_file, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @property
    def milvus_host(self) -> str:
        return self.config.get("MILVUS_HOST", "localhost")

    @property
    def milvus_port(self) -> int:
        return int(self.config.get("MILVUS_PORT", 19530))

    @property
    def collection_name(self) -> str:
        return self.config.get("COLLECTION_NAME", "kedb_collection")    


class VectorDB:
    def __init__(self, config_file: str = "rag/config.yaml"):
        config = Config(config_file)
        self.host = config.milvus_host
        self.port = config.milvus_port
        self.default_collection_name = config.collection_name

        self.collection: Optional[Collection] = None
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            return

        self.client = OpenAI(api_key=api_key)
        
        logger.info("VectorDB initialized with host={}, port={}, default_collection={}", 
                    self.host, self.port, self.default_collection_name)

    def connect(self, collection_name: Optional[str] = None):
        try:
            connections.connect(host=self.host, port=self.port)
            logger.info("Connected to Milvus at {}:{}", self.host, self.port)

            self.create_collection(collection_name)
        except Exception as e:
            logger.exception("Failed to connect to Milvus: {}", e)
            raise

    def disconnect(self):
        try:
            connections.disconnect("default")
            logger.warning("Disconnected from Milvus")
        except Exception as e:
            logger.exception("Error while disconnecting from Milvus: {}", e)

    def ingest(self, kedb_data: List[Dict[str, Any]], collection_name: Optional[str] = None):        
        if collection_name:
            self.collection = Collection(collection_name)

        if not self.collection:
            logger.error("Collection not initialized. Call connect() first or specify collection_name.")
            raise RuntimeError("Collection not initialized. Call connect() first or specify collection_name.")

        schema_fields = [f.name for f in self.collection.schema.fields if f.name not in ("embedding", "id")]
        logger.debug("Schema fields (excluding embedding): {}", schema_fields)

        field_data = {field: [] for field in schema_fields}
        embeddings = []

        for idx, entry in enumerate(kedb_data, start=1):
            text_to_embed = f"{entry.get('title', '')} {entry.get('description', '')}".strip()
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text_to_embed
                )
                embedding = response.data[0].embedding
                embeddings.append(embedding)

                for field in schema_fields:
                    field_data[field].append(entry.get(field, None))

                logger.debug("Processed entry {} -> title='{}'", idx, entry.get("title", ""))
            except Exception as e:
                logger.exception("Error generating embedding for entry {}: {}", idx, e)

        insert_data = [field_data[field] for field in schema_fields] + [embeddings]

        try:
            self.collection.insert(insert_data)
            logger.success("Inserted {} records into '{}'", len(kedb_data), self.collection.name)
        except Exception as e:
            logger.exception("Failed to insert data into collection '{}': {}", self.collection.name, e)

    def create_index(self, collection_name: Optional[str] = None):        
        if collection_name:
            self.collection = Collection(collection_name)

        if not self.collection:
            logger.error("Collection not initialized. Call connect() first or specify collection_name.")
            raise RuntimeError("Collection not initialized. Call connect() first or specify collection_name.")

        try:
            self.collection.create_index(
                field_name="embedding",
                index_params={
                    "index_type": "IVF_FLAT",
                    "metric_type": "L2",
                    "params": {"nlist": 128}
                }
            )
            self.collection.load()
            logger.success("Index created and collection '{}' loaded into memory", self.collection.name)
        except Exception as e:
            logger.exception("Failed to create index on collection '{}': {}", self.collection.name, e)

    def create_collection(self, collection_name: Optional[str] = None):
        if not collection_name:
            collection_name = self.default_collection_name

        # Kiểm tra xem collection đã tồn tại chưa
        from pymilvus import utility
        if utility.has_collection(collection_name):
            logger.info("Collection '{}' already exists", collection_name)
            self.collection = Collection(collection_name)
            return

        # Định nghĩa schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="root_cause", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="solution", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),            
        ]
        schema = CollectionSchema(fields, description="KEDB collection")
        self.collection = Collection(name=collection_name, schema=schema)
        logger.success("Collection '{}' created", collection_name)

    def query(self, text: str, top_k: int = 3, collection_name: Optional[str] = None):        
        if collection_name:
            self.collection = Collection(collection_name)

        if not self.collection:
            logger.error("Collection not initialized. Call connect() first or specify collection_name.")
            raise RuntimeError("Collection not initialized. Call connect() first or specify collection_name.")

        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            query_vector = response.data[0].embedding
            logger.debug("Generated query embedding for text='{}'", text[:50])

            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "L2", "params": {"nprobe": 10}},
                limit=top_k,
                output_fields=["id", "title", "description", "solution", "root_cause"]
            )

            logger.info("Query executed on '{}': top_k={}", self.collection.name, top_k)
            return results[0] # type: ignore
        except Exception as e:
            logger.exception("Failed to query collection '{}': {}", self.collection.name, e)
            raise
