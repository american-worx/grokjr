from pydantic import BaseModel
from datetime import datetime

class Permission(BaseModel):
    id: int | None = None
    action: str
    status: str
    timestamp: datetime = datetime.now()