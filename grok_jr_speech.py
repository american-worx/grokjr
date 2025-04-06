import logging
import asyncio
from grok_jr.app.speech.speech_module import GrokJrSpeechModule
from grok_jr.app.dependencies import get_inference_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    inference_engine = get_inference_engine()
    speech_module = GrokJrSpeechModule()
    asyncio.run(speech_module.run())  # Already async, no change needed