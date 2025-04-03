import time
import websockets
import asyncio
import json
import logging
from grok_jr.app.speech.utils import AudioUtils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, uri: str = "ws://localhost:8000/stream"):
        self.uri = uri
        self.audio_utils = AudioUtils(speech_dir="speech/")

    async def run(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                # Record audio
                input_file = f"input_{int(time.time())}.wav"
                input_path = self.audio_utils.record_audio(input_file, duration=5)

                # Send audio path to server
                message = json.dumps({"audio_path": input_path})
                await websocket.send(message)
                logger.info(f"Sent audio path: {input_path}")

                # Receive response
                response = await websocket.recv()
                data = json.loads(response)
                output_path = data.get("audio_path")

                if output_path:
                    logger.info(f"Received audio path: {output_path}")
                    self.audio_utils.play_audio(output_path)
                    self.audio_utils.delete_audio(output_path)
                else:
                    logger.error(f"Failed to receive audio path: {data}")

                # Clean up
                self.audio_utils.delete_audio(input_path)
        except websockets.exceptions.ConnectionClosedOK as e:
            logger.info("WebSocket connection closed normally: {e}")
        except Exception as e:
            logger.error(f"Error in WebSocket client: {str(e)}")
            raise

if __name__ == "__main__":
    client = WebSocketClient()
    asyncio.run(client.run())