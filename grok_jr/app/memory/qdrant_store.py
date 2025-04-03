# In app/memory/qdrant_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
import logging

class QdrantStore:
    def __init__(self, collection_name: str = "interactions"):
        self.logger = logging.getLogger(__name__)
        self.client = QdrantClient("localhost", port=6333)  # Server mode
        self.collection_name = collection_name
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self._initialize_collection()

    def _initialize_collection(self):
        try:
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
                self.logger.info(f"Created new Qdrant collection: {self.collection_name}")
            else:
                collection_info = self.client.get_collection(self.collection_name)
                self.logger.info(f"Using existing Qdrant collection: {self.collection_name}, Points: {collection_info.points_count}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Qdrant collection: {str(e)}")
            raise

    def add_embedding(self, text: str, payload: dict):
        try:
            vector = self.encoder.encode(text).tolist()
            point_id = payload["id"]
            self.logger.info(f"Adding embedding with ID: {point_id}, Payload: {payload}")
            response = self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            self.logger.info(f"Added embedding for text: {text[:50]}..., Qdrant response: {response}")
        except Exception as e:
            self.logger.error(f"Failed to add embedding: {str(e)}")
            raise

    def search(self, query: str, limit: int = 3) -> list:
        try:
            query_vector = self.encoder.encode(query).tolist()
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return results
        except Exception as e:
            self.logger.error(f"Failed to search Qdrant: {str(e)}")
            return []