import asyncio
import logging
from datetime import datetime
from fastapi import WebSocket
from grok_jr.app.memory.sqlite_store import SQLiteStore
from grok_jr.app.config.settings import settings

class SwarmManager:
    def __init__(self, sqlite_store: SQLiteStore):
        self.logger = logging.getLogger(__name__)
        self.sqlite_store = sqlite_store
        self.websocket_clients = {}  # {agent_id: WebSocket}
        self.register_agent("grok_jr", "coordinator")

    def register_agent(self, agent_id: str, role: str):
        self.sqlite_store.register_agent(agent_id, role)

    async def delegate_task(self, task: dict) -> str:
        available_agents = self.sqlite_store.query_sql(
            "SELECT agent_id FROM agents WHERE status = 'online' AND agent_id != 'grok_jr'"
        )
        if not available_agents:
            self.logger.info("No agents available for delegation.")
            return "NO_AGENTS_AVAILABLE"

        for agent in available_agents:
            agent_id = agent["agent_id"]
            if agent_id in self.websocket_clients:
                try:
                    await self.websocket_clients[agent_id].send_json(task)
                    response = await asyncio.wait_for(
                        self.websocket_clients[agent_id].receive_text(),
                        timeout=settings.SWARM_TIMEOUT
                    )
                    self.logger.info(f"Agent '{agent_id}' responded: {response}")
                    return response
                except (asyncio.TimeoutError, Exception) as e:
                    self.logger.warning(f"Agent '{agent_id}' failed: {str(e)}")
                    self.sqlite_store.update_agent_status(agent_id, "offline")
        self.logger.info("No agents responded in time.")
        return "NO_RESPONSE"

    async def handle_swarm(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        self.websocket_clients[agent_id] = websocket
        self.sqlite_store.update_agent_status(agent_id, "online")
        try:
            while True:
                await websocket.receive_text()  # Keep connection alive
        except Exception as e:
            self.logger.info(f"Agent '{agent_id}' disconnected: {str(e)}")
            del self.websocket_clients[agent_id]
            self.sqlite_store.update_agent_status(agent_id, "offline")