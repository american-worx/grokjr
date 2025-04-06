from pydantic import BaseModel
from datetime import datetime

class Skill(BaseModel):
    id: int | None = None
    name: str
    description: str | None = None  # Add this
    instructions: str
    code: str | None = None
    timestamp: datetime = datetime.now()
    acquired: str = "false"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }