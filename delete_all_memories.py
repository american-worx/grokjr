import qdrant_client
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Qdrant client
client = qdrant_client.QdrantClient(host="localhost", port=6333)

def delete_all_memories():
    try:
        client.delete_collection(collection_name="auto_ninja_memory")
        logger.info("Successfully deleted the entire auto_ninja_memory collection")
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")

if __name__ == "__main__":
    delete_all_memories()