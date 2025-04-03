# In app/dependencies.py

from grok_jr.app.memory.sqlite_store import SQLiteStore
from grok_jr.app.memory.qdrant_store import QdrantStore
from grok_jr.app.inference.engine import InferenceEngine

sqlite_store = SQLiteStore()
inference_engine = InferenceEngine()
qdrant_store_interactions = QdrantStore(collection_name="interactions")  # Uses localhost:6333 by default
qdrant_store_skills = QdrantStore(collection_name="skills")

def get_sqlite_store() -> SQLiteStore:
    return sqlite_store

def get_inference_engine() -> InferenceEngine:
    return inference_engine

def get_qdrant_store_interactions() -> QdrantStore:
    return qdrant_store_interactions

def get_qdrant_store_skills() -> QdrantStore:
    return qdrant_store_skills