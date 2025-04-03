from pydantic import BaseModel

class Response(BaseModel):
    prediction: str
    status: str