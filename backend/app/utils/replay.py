import uuid
import os
import shutil
from typing import List, Dict, Any
from backend.app.database import get_duckdb_conn
from backend.app.utils.serialization import save_world, load_world

class ReplayEngine:
    """Queries historical logs from DuckDB for event search and visualization"""
    
    @staticmethod
    def get_event_timeline(world_id: str, start_tick: int, end_tick: int) -> List[Dict[str, Any]]:
        """Retrieve historical log of events between ticks"""
        conn = get_duckdb_conn()
        try:
            res = conn.execute(
                """
                SELECT event_id, tick, event_type, source_entity_id, description, metadata, timestamp 
                FROM simulation_events 
                WHERE world_id = ? AND tick >= ? AND tick <= ?
                ORDER BY tick ASC, timestamp ASC
                """,
                (world_id, start_tick, end_tick)
            ).fetchall()
            
            timeline = []
            for row in res:
                timeline.append({
                    "event_id": row[0],
                    "tick": row[1],
                    "event_type": row[2],
                    "source_id": row[3],
                    "description": row[4],
                    "metadata": row[5],
                    "timestamp": row[6]
                })
            return timeline
        finally:
            conn.close()

    @staticmethod
    def fork_world(source_world_dir: str, new_world_name: str) -> str:
        """
        Forks/branches a timeline: copies the source snapshot parquet files 
        and re-registers a brand new world ID, decoupling futures.
        """
        new_world_id = str(uuid.uuid4())
        
        # Determine parent dir
        parent_dir = os.path.dirname(source_world_dir)
        new_world_dir = os.path.join(parent_dir, f"world_{new_world_id}")
        
        # Copy snapshot files
        shutil.copytree(source_world_dir, new_world_dir)
        
        # Update metadata JSON inside new copy
        meta_path = os.path.join(new_world_dir, "metadata.json")
        if os.path.exists(meta_path):
            import json
            with open(meta_path, "r") as f:
                meta = json.load(f)
            
            meta["world_id"] = new_world_id
            meta["name"] = new_world_name
            
            with open(meta_path, "w") as f:
                json.dump(meta, f)
                
        return new_world_id
