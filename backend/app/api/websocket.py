import json
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.event_bus import event_bus

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                # Connection might be dead, clean up later or ignore
                pass

manager = ConnectionManager()

# Link the connection manager's broadcast to the event bus
async def ws_event_listener(event: dict):
    # Broadcast event payload to all clients
    await manager.broadcast({
        "type": "SIM_EVENT",
        "payload": event
    })

event_bus.subscribe(ws_event_listener)

@router.websocket("/ws/simulation/{world_id}")
async def websocket_endpoint(websocket: WebSocket, world_id: str):
    await manager.connect(websocket)
    try:
        # Send initial confirmation
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "world_id": world_id
        }))
        
        while True:
            # Maintain connection and listen for client commands (e.g. Pause, Play, Speed up)
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                # Dispatch commands if necessary
                # We can communicate speed changes to the engine scheduler
                # example: {"action": "SET_SPEED", "multiplier": 10}
                await manager.broadcast({
                    "type": "CLIENT_COMMAND",
                    "sender": str(websocket.client),
                    "command": command
                })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
