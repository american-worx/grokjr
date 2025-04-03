from pydantic import BaseModel
from datetime import datetime

class Skill(BaseModel):
    id: int | None = None
    name: str
    instructions: str
    code: str | None = None
    timestamp: datetime = datetime.now()