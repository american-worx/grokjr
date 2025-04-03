from sentence_transformers import SentenceTransformer
import logging

class MemoryUtils:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

    def summarize(self, text: str, max_length: int = 100) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def generate_embedding(self, text: str) -> list:
        try:
            return self.encoder.encode(text).tolist()
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            return []

    def get_context(self, sqlite_store, limit: int = 3) -> str:
        interactions = sqlite_store.get_last_interactions(limit)
        context = "Recent interactions:\n"
        for prompt, response in interactions:
            context += f"Prompt: {prompt}\nResponse: {response}\n"
        return context