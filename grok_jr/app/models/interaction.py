# In app/models/interaction.py

from pydantic import BaseModel
from datetime import datetime

class Interaction(BaseModel):
    id: int | None = None
    user_prompt: str
    local_response: str  # New field for local agent's inference
    response: str        # Final merged response (from Grok or local fallback)
    timestamp: datetime = datetime.now()