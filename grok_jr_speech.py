# In grok_jr_speech.py

import logging
from grok_jr.app.speech.speech_module import GrokJrSpeechModule
from grok_jr.app.dependencies import get_inference_engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Use singleton InferenceEngine
    inference_engine = get_inference_engine()
    speech_module = GrokJrSpeechModule()  # InferenceEngine is already singleton via dependencies
    speech_module.run()