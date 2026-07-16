import uuid
import random
from typing import Dict, List, Any
from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation

from backend.app.core.spatial import SpatialMap
from backend.app.core.event_bus import event_bus
from backend.app.models.world import WorldModel
from backend.app.models.citizen import CitizenModel
from backend.app.database import SessionLocal

class CitizenAgent(Agent):
    """Mesa Agent representing a dynamic AI Citizen"""
    def __init__(self, unique_id: str, model: Model, name: str, age: float, wealth: float):
        super().__init__(unique_id, model)
        self.name = name
        self.age = age
        self.health = 100.0
        self.wealth = wealth
        self.occupation = "Forager"
        self.inventory: Dict[str, float] = {"food": 5.0, "wood": 0.0, "stone": 0.0, "iron": 0.0}
        
        # Big Five Personality
        self.personality = {
            "o": random.random(),
            "c": random.random(),
            "e": random.random(),
            "a": random.random(),
            "n": random.random()
        }
        
        # DNA represented as character codes
        self.dna = "".join(random.choices("ATCG", k=32))
        
        # Needs
        self.hunger = 0.0  # 0 to 100

    def step(self):
        """Action execution loop during a tick"""
        if self.health <= 0:
            return

        # Aging and hunger increases
        self.age += 0.1
        self.hunger += 5.0
        
        # Decouple behavior to cognitive planner or heuristic fallback
        self.execute_heuristics()
        
        # Resolve basic starvation
        if self.hunger > 80:
            if self.inventory["food"] >= 1.0:
                self.inventory["food"] -= 1.0
                self.hunger = max(0.0, self.hunger - 30.0)
            else:
                self.health -= 5.0 # Health decays due to starvation
                
        if self.health <= 0:
            self.die("Starvation")

    def execute_heuristics(self):
        """Standard rule-based backup behavioral logic"""
        # Search for resources or move randomly
        x, y = self.pos
        terrain_map = self.model.spatial_map
        
        # If hungry, try to forage food from plain tiles
        if self.hunger > 40 and terrain_map.food_nodes[x, y] > 0:
            harvest = min(terrain_map.food_nodes[x, y], 2.0)
            terrain_map.food_nodes[x, y] -= harvest
            self.inventory["food"] += harvest
            event_bus.publish(
                "FORAGED_FOOD", 
                self.model.world_id, 
                self.model.tick_counter, 
                source_id=self.unique_id,
                description=f"{self.name} foraged {harvest:.1f} food units.",
                metadata={"amount": harvest}
            )
        else:
            # Move towards a random cell
            possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
            new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)
            
            event_bus.publish(
                "MOVED", 
                self.model.world_id, 
                self.model.tick_counter, 
                source_id=self.unique_id,
                description=f"{self.name} moved to {new_position}.",
                metadata={"new_pos": new_position}
            )

    def die(self, cause: str):
        self.health = 0
        event_bus.publish(
            "DIED", 
            self.model.world_id, 
            self.model.tick_counter, 
            source_id=self.unique_id,
            description=f"{self.name} has died of {cause}.",
            metadata={"cause": cause}
        )
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)


class CivilizationEngine(Model):
    """Headless simulation core managing map, schedule, and time progression"""
    def __init__(self, world_id: str, name: str, seed: int, width: int, height: int):
        super().__init__()
        self.world_id = world_id
        self.world_name = name
        self.tick_counter = 0
        self.reset_randomizer(seed)
        
        self.spatial_map = SpatialMap(width, height, seed)
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        
        # Populate database record
        self._save_world_state()

    def add_citizen(self, name: str, age: float, wealth: float, pos: tuple = None) -> CitizenAgent:
        citizen_id = str(uuid.uuid4())
        agent = CitizenAgent(citizen_id, self, name, age, wealth)
        self.schedule.add(agent)
        
        if pos is None:
            # Place in a random valid coordinate
            pos = (random.randint(0, self.spatial_map.width - 1), random.randint(0, self.spatial_map.height - 1))
            
        self.grid.place_agent(agent, pos)
        
        # Write relational citizen state record
        db = SessionLocal()
        try:
            cit_model = CitizenModel(
                id=agent.unique_id,
                world_id=self.world_id,
                name=agent.name,
                age=agent.age,
                wealth=agent.wealth,
                pos_x=pos[0],
                pos_y=pos[1],
                personality_o=agent.personality["o"],
                personality_c=agent.personality["c"],
                personality_e=agent.personality["e"],
                personality_a=agent.personality["a"],
                personality_n=agent.personality["n"],
                dna_sequence=agent.dna,
                is_alive=True
            )
            db.add(cit_model)
            db.commit()
        finally:
            db.close()
            
        event_bus.publish(
            "SPAWNED", 
            self.world_id, 
            self.tick_counter, 
            source_id=citizen_id,
            description=f"{name} spawned in the civilization.",
            metadata={"coords": pos}
        )
        return agent

    def step(self):
        """Advance the simulation grid and agents by one tick"""
        self.tick_counter += 1
        
        # Tick climate, resources and agents
        self.spatial_map.tick_weather()
        self.schedule.step()
        
        # Persist world tick count to SQLite
        self._save_world_state()
        
        # Trigger generic event tick heartbeat
        event_bus.publish(
            "TICK_HEARTBEAT", 
            self.world_id, 
            self.tick_counter,
            description=f"Simulation advanced to tick {self.tick_counter}.",
            metadata={"weather": self.spatial_map.weather}
        )

    def _save_world_state(self):
        db = SessionLocal()
        try:
            world = db.query(WorldModel).filter(WorldModel.id == self.world_id).first()
            if not world:
                world = WorldModel(id=self.world_id, name=self.world_name, seed=self.random.randint(0, 1000000), current_tick=self.tick_counter)
                db.add(world)
            else:
                world.current_tick = self.tick_counter
            db.commit()
        finally:
            db.close()
