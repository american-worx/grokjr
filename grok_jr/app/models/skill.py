from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Skill(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    instructions: str
    code: Optional[str] = None
    required_params: Optional[str] = None  # JSON string, e.g., '{"task": "str", "duration": "int"}'
    timestamp: datetime = datetime.now()
    acquired: str = "false"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }