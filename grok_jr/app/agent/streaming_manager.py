import json
import logging
import time
from fastapi import WebSocket
from grok_jr.app.speech.stt import STT
from grok_jr.app.speech.tts import TTS
from grok_jr.app.speech.utils import AudioUtils
from grok_jr.app.memory.sqlite_store import SQLiteStore
from grok_jr.app.memory.qdrant_store import QdrantStore
from grok_jr.app.inference.engine import InferenceEngine

class StreamingManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stt = STT(model_name="small")
        self.tts = TTS(engine="gTTS", speech_dir="speech/")
        self.audio_utils = AudioUtils(speech_dir="speech/")
        self.sqlite_store = SQLiteStore()
        self.qdrant_store = QdrantStore(collection_name="interactions")
        self.inference_engine = InferenceEngine()

    async def handle_stream(self, websocket: WebSocket, path):
        try:
            # Receive one message
            message = await websocket.receive_json()
            audio_path = message.get("audio_path")

            if not audio_path:
                await websocket.send_json({"error": "No audio path provided"})
                return

            # Transcribe audio (force English)
            prompt = self.stt.transcribe(audio_path, language="en")  # Add language="en"
            if not prompt:
                await websocket.send_json({"error": "Failed to transcribe audio"})
                return

            # Get prediction
            has_permission = self.sqlite_store.get_permission("access_xai_api") == "granted"
            prediction = self.inference_engine.predict(prompt, use_xai_api=has_permission)

            # Log interaction
            self.sqlite_store.add_interaction(prompt, prediction)
            self.qdrant_store.add_embedding(prompt, {"id": int(time.time()), "prompt": prompt, "response": prediction})

            # Convert response to speech
            output_file = f"output_{int(time.time())}.mp3"
            output_path = self.tts.text_to_speech(prediction, output_file)
            if not output_path:
                await websocket.send_json({"error": "Failed to generate speech"})
                return

            # Send audio path back to client
            await websocket.send_json({"audio_path": output_path})

        except Exception as e:
            self.logger.error(f"Error in WebSocket stream: {str(e)}")
            await websocket.send_json({"error": str(e)})