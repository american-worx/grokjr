# In app/main.py

from fastapi import FastAPI
from grok_jr.app.config.settings import settings
from grok_jr.app.api.endpoints import router
from grok_jr.app.dependencies import get_sqlite_store, get_inference_engine
from grok_jr.app.agent.skill_manager import SkillManager
import logging

app = FastAPI(title="Grok Jr. API")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SkillManager (uses singleton InferenceEngine internally)
skill_manager = SkillManager()

# Access singletons directly
sqlite_store = get_sqlite_store()
inference_engine = get_inference_engine()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Grok Jr. API...")

    if not settings.XAI_API_KEY:
        logger.error("XAI_API_KEY not set. Grok Jr. requires it to function.")
        raise RuntimeError("XAI_API_KEY not set.")

    sqlite_store.set_status("first_run", "true")
    logger.info("Grok Jr. initialized as the Adaptive Skill Master and Continuous Learning Facilitator.")
    sqlite_store.set_status("first_run", "false")

# Include API router
app.include_router(router)