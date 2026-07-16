import json
import random
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.core.event_bus import event_bus
from backend.app.core.scheduler import scheduler
from backend.app.core.engine import CivilizationEngine, CitizenAgent

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
                pass

manager = ConnectionManager()

# Link the connection manager's broadcast to the event bus
async def ws_event_listener(event: dict):
    await manager.broadcast({
        "type": "SIM_EVENT",
        "payload": event
    })

event_bus.subscribe(ws_event_listener)

@router.websocket("/ws/simulation/{world_id}")
async def websocket_endpoint(websocket: WebSocket, world_id: str):
    await manager.connect(websocket)
    try:
        # Automatically initialize and register world if it doesn't exist
        if world_id not in scheduler.active_simulations:
            engine = CivilizationEngine(world_id=world_id, name="Demo Civilization", seed=42, width=50, height=50)
            
            # Add initial citizens
            names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta", "Iota", "Kappa"]
            for name in names:
                engine.add_citizen(name=name, age=20.0 + random.uniform(0, 10), wealth=50.0)
                
            scheduler.register_world(world_id, engine)
            scheduler.start(world_id)
        else:
            engine = scheduler.active_simulations[world_id]
            
        # Construct terrain layout
        terrain_grid = []
        for x in range(engine.spatial_map.width):
            row = []
            for y in range(engine.spatial_map.height):
                row.append(int(engine.spatial_map.terrain[x, y]))
            terrain_grid.append(row)
            
        # Get current citizens info
        citizens_dict = {}
        for agent in engine.schedule.agents:
            if isinstance(agent, CitizenAgent):
                citizens_dict[agent.unique_id] = {
                    "id": agent.unique_id,
                    "name": agent.name,
                    "age": agent.age,
                    "health": agent.health,
                    "wealth": agent.wealth,
                    "pos_x": agent.pos[0],
                    "pos_y": agent.pos[1],
                    "occupation": agent.occupation,
                    "is_sick": agent.is_sick
                }

        # Send initial confirmation including the layout and starting citizens
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "world_id": world_id,
            "width": engine.spatial_map.width,
            "height": engine.spatial_map.height,
            "terrain": terrain_grid,
            "citizens": citizens_dict
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                action = command.get("action")
                if action == "SET_SPEED":
                    scheduler.set_speed(world_id, float(command.get("multiplier", 1)))
                elif action == "STEP":
                    scheduler.step_once(world_id)
                elif action == "SUMMON_DISASTER":
                    disaster_type = command.get("disaster_type")
                    cx = int(command.get("x", 25))
                    cy = int(command.get("y", 25))
                    engine.summon_disaster(disaster_type, cx, cy)
                    
                # Also broadcast command to other clients
                await manager.broadcast({
                    "type": "CLIENT_COMMAND",
                    "sender": str(websocket.client),
                    "command": command
                })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

