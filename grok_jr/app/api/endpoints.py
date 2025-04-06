from fastapi import APIRouter, Depends, WebSocket
from grok_jr.app.agent.swarm_MANAGER import SwarmManager
from grok_jr.app.config import settings
from grok_jr.app.dependencies import get_sqlite_store, get_inference_engine
from grok_jr.app.inference.engine import InferenceEngine
from grok_jr.app.memory.sqlite_store import SQLiteStore
from grok_jr.app.agent.streaming_manager import StreamingManager

router = APIRouter()
streaming_manager = StreamingManager()
swarm_manager = None 

@router.post("/predict")
async def predict(
    message: dict,
    sqlite_store: SQLiteStore = Depends(get_sqlite_store),
    inference_engine: InferenceEngine = Depends(get_inference_engine)
):
    prompt = message.get("message", "")
    if not prompt:
        return {"prediction": "No message provided.", "status": "error"}

    # Process the prompt (always using xAI API since internet access is mandatory)
    response = inference_engine.predict(prompt, use_xai_api=True)

    # Log interaction
    sqlite_store.add_interaction(prompt, response)

    return {"prediction": response, "status": "success"}

@router.websocket("/stream")
async def stream(websocket: WebSocket):
    await websocket.accept()
    try:
        await streaming_manager.handle_stream(websocket, None)
    finally:
        await websocket.close()

@router.websocket("/swarm/stream")
async def swarm_stream(websocket: WebSocket, agent_id: str = "unknown"):
    global swarm_manager
    if not settings.SWARM_MODE:
        await websocket.close(code=1000, reason="Swarm mode disabled")
        return
    if not swarm_manager:
        swarm_manager = SwarmManager(get_sqlite_store())
    await swarm_manager.handle_swarm(websocket, agent_id)