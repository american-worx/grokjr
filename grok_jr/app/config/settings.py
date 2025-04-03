import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Determine the absolute path to the .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # Navigate up to grok_jr/
env_path = BASE_DIR / ".env"

# Load the .env file
load_dotenv(env_path)

class Settings(BaseSettings):
    # Model settings
    MODEL_NAME: str = "google/gemma-3-1b-it"
    XAI_API_KEY: str | None = None
    GROK_URL: str = "https://api.x.ai/v1/chat/completions"
    HF_TOKEN: Optional[str] = None
    # Speech settings
    WHISPER_MODEL: str = "tiny"
    TTS_ENGINE: str = "gTTS"  # Fallback to "pyttsx3" if offline
    SPEECH_DIR: str = "speech/"

    class Config:
        env_file = ".env"  # Still keep this for Pydantic, but it’s now redundant
        env_file_encoding = "utf-8"

# Debug: Print the loaded XAI_API_KEY to verify
settings = Settings()
print(f"Loaded XAI_API_KEY: {settings.XAI_API_KEY}")