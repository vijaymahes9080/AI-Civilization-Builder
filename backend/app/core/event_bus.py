import json
import uuid
import datetime
import asyncio
from typing import Dict, Set, Callable, Any
from backend.app.database import get_duckdb_conn

class EventBus:
    def __init__(self):
        self._listeners: Set[Callable[[Dict[str, Any]], None]] = set()
        self._loop = asyncio.get_event_loop()

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe a callback function to receive all published events"""
        self._listeners.add(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Unsubscribe a callback function"""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def publish(self, event_type: str, world_id: str, tick: int, source_id: str = None, target_id: str = None, description: str = "", metadata: Dict[str, Any] = None):
        """Publish an event to all subscribers and write to DuckDB event log"""
        event_id = str(uuid.uuid4())
        event_data = {
            "event_id": event_id,
            "world_id": world_id,
            "tick": tick,
            "event_type": event_type,
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "description": description,
            "metadata": metadata or {},
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        # Write asynchronously to DuckDB
        self._write_to_duckdb(event_data)

        # Notify all active in-process listeners (e.g., WebSocket connections)
        for listener in list(self._listeners):
            try:
                if asyncio.iscoroutinefunction(listener):
                    asyncio.create_task(listener(event_data))
                else:
                    listener(event_data)
            except Exception as e:
                print(f"Error executing listener: {e}")

    def _write_to_duckdb(self, event: Dict[str, Any]):
        """Save event to DuckDB time-series event log"""
        try:
            conn = get_duckdb_conn()
            # Convert metadata dict to JSON string for DuckDB
            metadata_str = json.dumps(event["metadata"])
            
            conn.execute(
                """
                INSERT INTO simulation_events (
                    event_id, world_id, tick, event_type, 
                    source_entity_id, target_entity_id, description, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["world_id"],
                    event["tick"],
                    event["event_type"],
                    event["source_entity_id"],
                    event["target_entity_id"],
                    event["description"],
                    metadata_str
                )
            )
            conn.close()
        except Exception as e:
            print(f"Failed to log event to DuckDB: {e}")

# Global Event Bus Singleton
event_bus = EventBus()
