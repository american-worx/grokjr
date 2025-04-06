import logging
import whisper
import torch

logger = logging.getLogger(__name__)

class STT:
    def __init__(self, model_name: str = "base"):
        logger.info(f"Initializing STT with Whisper...")
        try:
            # Try loading on CUDA first
            self.model = whisper.load_model(model_name, device="cuda")
            logger.info(f"Loaded Whisper model '{model_name}' on CUDA.")
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.warning(f"CUDA out of memory: {str(e)}. Falling back to CPU.")
                self.model = whisper.load_model(model_name, device="cpu")
                logger.info(f"Loaded Whisper model '{model_name}' on CPU.")
            else:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {str(e)}")
            raise

    def transcribe(self, audio_path: str) -> str:
        try:
            result = self.model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return ""