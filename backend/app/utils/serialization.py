import json
import os
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from typing import Dict, Any
from backend.app.core.engine import CivilizationEngine, CitizenAgent

def save_world(engine: CivilizationEngine, base_path: str):
    """
    Serializes simulation engine state (grid map, citizens, market) 
    into Parquet files for fast, local-first recovery.
    """
    os.makedirs(base_path, exist_ok=True)
    
    # 1. Serialize map layout (terrain and resource matrices)
    map_data = {
        "x": [], "y": [], "terrain": [], "food": [], "wood": [], "stone": [], "iron": []
    }
    for x in range(engine.spatial_map.width):
        for y in range(engine.spatial_map.height):
            map_data["x"].append(x)
            map_data["y"].append(y)
            map_data["terrain"].append(int(engine.spatial_map.terrain[x, y]))
            map_data["food"].append(float(engine.spatial_map.food_nodes[x, y]))
            map_data["wood"].append(float(engine.spatial_map.wood_nodes[x, y]))
            map_data["stone"].append(float(engine.spatial_map.stone_nodes[x, y]))
            map_data["iron"].append(float(engine.spatial_map.iron_nodes[x, y]))
            
    df_map = pd.DataFrame(map_data)
    table_map = pa.Table.from_pandas(df_map)
    pq.write_table(table_map, os.path.join(base_path, "map.parquet"))

    # 2. Serialize Citizen Agents
    agent_data = []
    for agent in engine.schedule.agents:
        if isinstance(agent, CitizenAgent):
            agent_data.append({
                "id": agent.unique_id,
                "name": agent.name,
                "age": agent.age,
                "health": agent.health,
                "wealth": agent.wealth,
                "pos_x": agent.pos[0],
                "pos_y": agent.pos[1],
                "inventory": json.dumps(agent.inventory),
                "personality": json.dumps(agent.personality),
                "dna": agent.dna,
                "hunger": agent.hunger
            })
            
    df_agents = pd.DataFrame(agent_data)
    table_agents = pa.Table.from_pandas(df_agents)
    pq.write_table(table_agents, os.path.join(base_path, "citizens.parquet"))

    # 3. Serialize general metadata
    meta = {
        "world_id": engine.world_id,
        "name": engine.world_name,
        "tick": engine.tick_counter,
        "width": engine.spatial_map.width,
        "height": engine.spatial_map.height,
        "seed": engine.spatial_map.seed
    }
    with open(os.path.join(base_path, "metadata.json"), "w") as f:
        json.dump(meta, f)


def load_world(base_path: str) -> CivilizationEngine:
    """Loads world layout and agent arrays from Parquet directories"""
    # Read metadata
    with open(os.path.join(base_path, "metadata.json"), "r") as f:
        meta = json.load(f)
        
    engine = CivilizationEngine(
        world_id=meta["world_id"],
        name=meta["name"],
        seed=meta["seed"],
        width=meta["width"],
        height=meta["height"]
    )
    engine.tick_counter = meta["tick"]

    # Reconstruct Map resources
    df_map = pq.read_table(os.path.join(base_path, "map.parquet")).to_pandas()
    for _, row in df_map.iterrows():
        x, y = int(row["x"]), int(row["y"])
        engine.spatial_map.terrain[x, y] = int(row["terrain"])
        engine.spatial_map.food_nodes[x, y] = float(row["food"])
        engine.spatial_map.wood_nodes[x, y] = float(row["wood"])
        engine.spatial_map.stone_nodes[x, y] = float(row["stone"])
        engine.spatial_map.iron_nodes[x, y] = float(row["iron"])

    # Reconstruct Agents
    # Clear automatically created citizens to prevent duplicates
    for agent in list(engine.schedule.agents):
        engine.grid.remove_agent(agent)
        engine.schedule.remove(agent)
        
    df_agents = pq.read_table(os.path.join(base_path, "citizens.parquet")).to_pandas()
    for _, row in df_agents.iterrows():
        agent = CitizenAgent(
            unique_id=row["id"],
            model=engine,
            name=row["name"],
            age=float(row["age"]),
            wealth=float(row["wealth"])
        )
        agent.health = float(row["health"])
        agent.inventory = json.loads(row["inventory"])
        agent.personality = json.loads(row["personality"])
        agent.dna = row["dna"]
        agent.hunger = float(row["hunger"])
        
        pos = (int(row["pos_x"]), int(row["pos_y"]))
        engine.schedule.add(agent)
        engine.grid.place_agent(agent, pos)
        
    return engine
