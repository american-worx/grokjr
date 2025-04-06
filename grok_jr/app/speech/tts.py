import os
import logging
from gtts import gTTS
import pyttsx3

class TTS:
    def __init__(self, engine: str = "gTTS", speech_dir: str = "speech/"):
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        self.speech_dir = speech_dir

        # Ensure the speech directory exists
        if not os.path.exists(self.speech_dir):
            os.makedirs(self.speech_dir)

        # Initialize the TTS engine (always use gTTS since internet access is mandatory)
        if self.engine == "gTTS":
            self.logger.info("Using gTTS for text-to-speech.")
        else:
            self.logger.error("Invalid engine specified. gTTS is required as internet access is mandatory.")
            raise ValueError("Invalid engine specified. gTTS is required as internet access is mandatory.")

    def text_to_speech(self, text: str, output_file: str) -> str:
        """Convert text to speech and save to a file."""
        output_path = os.path.join(self.speech_dir, output_file)
        try:
            # Use gTTS
            tts = gTTS(text=text, lang="en")
            tts.save(output_path)
            self.logger.info(f"Generated speech with gTTS: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Failed to generate speech: {str(e)}")
            return None