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
from backend.app.agents.brain import CitizenBrain
from backend.app.agents.values import CitizenValues
from backend.app.agents.needs import CitizenNeeds

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
        
        # Sickness and burn status
        self.is_sick = False
        self.sickness_level = 0.0
        self.is_burning = False
        self.death_cause = None

        # Needs and values
        self.values = CitizenValues(self.dna, self.personality)
        self.needs = CitizenNeeds()
        self.brain = CitizenBrain(self.unique_id, self.name, self.values, self.needs)
        
        self.hunger = 0.0

    async def step(self):
        """Action execution loop during a tick"""
        if self.health <= 0:
            return

        # Aging
        self.age += 0.1
        
        # Calculate nearby citizens
        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True)
        nearby_count = len([n for n in neighbors if isinstance(n, CitizenAgent)]) - 1
        
        # Update needs
        self.needs.update_needs(is_sheltered=False, nearby_citizens=max(0, nearby_count))
        self.hunger = self.needs.hunger
        
        # Build environmental context for decision making
        env_ctx = self.get_environmental_context(neighbors)
        
        # Decouple behavior to cognitive planner or heuristic fallback
        decision = await self.brain.decide_action(self.model.tick_counter, env_ctx)
        
        # Process the action decision
        self.execute_decision(decision)
        
        # Resolve basic starvation and burns
        self.resolve_conditions()
                
        if self.health <= 0:
            self.die(self.death_cause or "Starvation")

    def get_environmental_context(self, neighbors) -> Dict[str, Any]:
        x, y = self.pos
        terrain_map = self.model.spatial_map
        
        # Find nearby citizens
        nearby_citizens_info = []
        for n in neighbors:
            if isinstance(n, CitizenAgent) and n.unique_id != self.unique_id:
                nearby_citizens_info.append({
                    "id": n.unique_id,
                    "name": n.name,
                    "pos": n.pos,
                    "health": n.health,
                    "is_sick": n.is_sick
                })
                
        # Surrounding cells data
        surrounding_cells = []
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True)
        for cx, cy in possible_steps:
            cell_data = terrain_map.get_cell_data(cx, cy)
            cell_data["on_fire"] = (cx, cy) in self.model.burning_cells
            surrounding_cells.append(cell_data)
            
        return {
            "inventory": self.inventory,
            "nearby_citizens": nearby_citizens_info,
            "weather": terrain_map.weather,
            "temperature": float(terrain_map.temperature[x, y]),
            "cells": surrounding_cells,
            "is_sick": self.is_sick,
            "is_burning": self.is_burning,
            "active_disasters": self.model.get_active_disasters_near(self.pos)
        }

    def execute_decision(self, decision: Dict[str, Any]):
        action_type = decision.get("action_type", "REST")
        target = decision.get("target_coordinate", list(self.pos))
        
        if target and isinstance(target, list) and len(target) == 2:
            tx = max(0, min(self.model.spatial_map.width - 1, int(target[0])))
            ty = max(0, min(self.model.spatial_map.height - 1, int(target[1])))
            target = (tx, ty)
        else:
            target = self.pos
            
        if action_type == "MOVE":
            step_pos = self._step_towards(target)
            self.model.grid.move_agent(self, step_pos)
            self.log_event("MOVED", f"{self.name} moved to {step_pos}.", {"new_pos": step_pos})
            
        elif action_type == "FORAGE":
            x, y = self.pos
            terrain_map = self.model.spatial_map
            if terrain_map.food_nodes[x, y] > 0:
                harvest = min(terrain_map.food_nodes[x, y], 2.0)
                terrain_map.food_nodes[x, y] -= harvest
                self.inventory["food"] += harvest
                self.log_event("FORAGED_FOOD", f"{self.name} foraged {harvest:.1f} food units.", {"amount": harvest})
            elif terrain_map.wood_nodes[x, y] > 0:
                harvest = min(terrain_map.wood_nodes[x, y], 2.0)
                terrain_map.wood_nodes[x, y] -= harvest
                self.inventory["wood"] += harvest
                self.log_event("FORAGED_WOOD", f"{self.name} gathered {harvest:.1f} wood.", {"amount": harvest})
            elif terrain_map.stone_nodes[x, y] > 0:
                harvest = min(terrain_map.stone_nodes[x, y], 2.0)
                terrain_map.stone_nodes[x, y] -= harvest
                self.inventory["stone"] += harvest
                self.log_event("FORAGED_STONE", f"{self.name} quarried {harvest:.1f} stone.", {"amount": harvest})
            elif terrain_map.iron_nodes[x, y] > 0:
                harvest = min(terrain_map.iron_nodes[x, y], 1.0)
                terrain_map.iron_nodes[x, y] -= harvest
                self.inventory["iron"] += harvest
                self.log_event("FORAGED_IRON", f"{self.name} mined {harvest:.1f} iron.", {"amount": harvest})
            else:
                possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                new_pos = self.random.choice(possible_steps)
                self.model.grid.move_agent(self, new_pos)
                self.log_event("MOVED", f"{self.name} moved randomly to {new_pos}.", {"new_pos": new_pos})
                
        elif action_type == "TALK":
            speech = decision.get("speech_content", "Hello!")
            self.log_event("TALK", f"{self.name} said: \"{speech}\"", {"speech": speech})
            
        elif action_type == "REST":
            self.needs.exhaustion = max(0.0, self.needs.exhaustion - 25.0)
            self.log_event("RESTED", f"{self.name} rested to recover energy.", {})
            
        elif action_type == "FLEE":
            step_pos = self._step_away(target)
            self.model.grid.move_agent(self, step_pos)
            self.log_event("FLED", f"{self.name} fled danger at {target} to {step_pos}.", {"fled_from": target, "new_pos": step_pos})
            
        elif action_type == "EXTINGUISH":
            if target in self.model.burning_cells:
                self.model.extinguish_fire(target)
                self.log_event("EXTINGUISHED_FIRE", f"{self.name} extinguished fire at {target}.", {"coords": target})
            elif self.pos in self.model.burning_cells:
                self.model.extinguish_fire(self.pos)
                self.log_event("EXTINGUISHED_FIRE", f"{self.name} extinguished fire at {self.pos}.", {"coords": self.pos})
            else:
                self.log_event("HEURISTIC_FAILED", f"{self.name} tried to extinguish fire but none was found at target.", {})
                
        elif action_type == "QUARANTINE":
            self.log_event("QUARANTINED", f"{self.name} quarantined to prevent virus spread.", {})
            
        elif action_type == "MEDICATE":
            x, y = self.pos
            terrain = self.model.spatial_map.terrain[x, y]
            if terrain in [1, 2]:  # Plain or Forest
                self.is_sick = False
                self.sickness_level = 0.0
                self.log_event("HEALED", f"{self.name} found healing herbs and is cured.", {})
            else:
                step_pos = self._move_to_terrain([1, 2])
                self.model.grid.move_agent(self, step_pos)
                self.log_event("MOVED", f"{self.name} searched for healing herbs and moved to {step_pos}.", {"new_pos": step_pos})

    def _step_towards(self, target: tuple) -> tuple:
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True)
        best_pos = self.pos
        best_dist = self._dist(self.pos, target)
        for p in possible_steps:
            d = self._dist(p, target)
            if d < best_dist:
                best_dist = d
                best_pos = p
        return best_pos

    def _step_away(self, target: tuple) -> tuple:
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        best_pos = self.pos
        best_dist = self._dist(self.pos, target)
        for p in possible_steps:
            d = self._dist(p, target)
            if d > best_dist:
                best_dist = d
                best_pos = p
        return best_pos

    def _move_to_terrain(self, terrain_types: List[int]) -> tuple:
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        for p in possible_steps:
            if self.model.spatial_map.terrain[p[0], p[1]] in terrain_types:
                return p
        return self.random.choice(possible_steps)

    def _dist(self, a: tuple, b: tuple) -> float:
        return ((a[0] - b[0])**2 + (a[1] - b[1])**2)**0.5

    def resolve_conditions(self):
        # Resolve basic starvation
        if self.hunger > 80:
            if self.inventory.get("food", 0.0) >= 1.0:
                self.inventory["food"] -= 1.0
                self.needs.hunger = max(0.0, self.needs.hunger - 30.0)
                self.hunger = self.needs.hunger
            else:
                self.health -= 8.0
                
        # Resolve fire burn status
        if self.pos in self.model.burning_cells:
            self.is_burning = True
        else:
            self.is_burning = False

    def log_event(self, event_type: str, description: str, metadata: dict):
        event_bus.publish(
            event_type,
            self.model.world_id,
            self.model.tick_counter,
            source_id=self.unique_id,
            description=description,
            metadata=metadata
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
        
        # Disaster Simulation states
        self.active_disasters = []
        self.burning_cells = {}
        
        # Populate database record
        self._save_world_state()

    def add_citizen(self, name: str, age: float, wealth: float, pos: tuple = None) -> CitizenAgent:
        citizen_id = str(uuid.uuid4())
        agent = CitizenAgent(citizen_id, self, name, age, wealth)
        self.schedule.add(agent)
        
        if pos is None:
            pos = (random.randint(0, self.spatial_map.width - 1), random.randint(0, self.spatial_map.height - 1))
            
        self.grid.place_agent(agent, pos)
        
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

    async def step(self):
        """Advance the simulation grid and agents by one tick"""
        self.tick_counter += 1
        
        # Tick climate, resources, disasters
        self.spatial_map.tick_weather()
        self.process_disasters()
        
        # Execute citizen agent logic asynchronously
        agents = list(self.schedule.agents)
        random.shuffle(agents)
        for agent in agents:
            if agent in self.schedule.agents:
                await agent.step()
        
        # Persist world tick count to SQLite
        self._save_world_state()
        
        # Trigger generic event tick heartbeat
        event_bus.publish(
            "TICK_HEARTBEAT", 
            self.world_id, 
            self.tick_counter,
            description=f"Simulation advanced to tick {self.tick_counter}.",
            metadata={
                "weather": self.spatial_map.weather,
                "active_disasters": self.active_disasters,
                "burning_cells": [list(k) for k in self.burning_cells.keys()]
            }
        )

    def summon_disaster(self, disaster_type: str, x: int, y: int):
        if disaster_type == "METEOR":
            self.active_disasters.append({
                "type": "METEOR",
                "x": x,
                "y": y,
                "ticks_remaining": 3
            })
            event_bus.publish(
                "DISASTER_SUMMONED",
                self.world_id,
                self.tick_counter,
                description=f"A METEOR strike is imminent at coordinate ({x}, {y})!",
                metadata={"disaster_type": "METEOR", "x": x, "y": y}
            )
        elif disaster_type == "EPIDEMIC":
            citizens_at_pos = [a for a in self.schedule.agents if isinstance(a, CitizenAgent) and a.pos == (x, y)]
            if not citizens_at_pos and self.schedule.agents:
                target_agent = self.random.choice(list(self.schedule.agents))
            elif citizens_at_pos:
                target_agent = citizens_at_pos[0]
            else:
                target_agent = None
                
            if target_agent:
                target_agent.is_sick = True
                target_agent.sickness_level = 20.0
                event_bus.publish(
                    "DISASTER_SUMMONED",
                    self.world_id,
                    self.tick_counter,
                    source_id=target_agent.unique_id,
                    description=f"A viral epidemic has broken out! {target_agent.name} is patient zero.",
                    metadata={"disaster_type": "EPIDEMIC", "patient_zero_id": target_agent.unique_id, "x": target_agent.pos[0], "y": target_agent.pos[1]}
                )
        elif disaster_type == "ACID_RAIN":
            self.active_disasters.append({
                "type": "ACID_RAIN",
                "x": x,
                "y": y,
                "ticks_remaining": 10
            })
            event_bus.publish(
                "DISASTER_SUMMONED",
                self.world_id,
                self.tick_counter,
                description="Acid Rain storm summoned! Corrosive elements are falling from the sky.",
                metadata={"disaster_type": "ACID_RAIN", "x": x, "y": y}
            )

    def process_disasters(self):
        surviving_disasters = []
        for d in self.active_disasters:
            d["ticks_remaining"] -= 1
            if d["type"] == "METEOR" and d["ticks_remaining"] == 0:
                mx, my = d["x"], d["y"]
                neighbors = self.grid.get_neighborhood((mx, my), moore=True, include_center=True)
                for cx, cy in neighbors:
                    self.burning_cells[(cx, cy)] = 8
                    agents = self.grid.get_cell_list_contents((cx, cy))
                    for a in agents:
                        if isinstance(a, CitizenAgent):
                            a.health -= 50.0
                            a.death_cause = "Meteor Blast"
                event_bus.publish(
                    "METEOR_IMPACT",
                    self.world_id,
                    self.tick_counter,
                    description=f"Meteor impacted at ({mx}, {my})! Fire is spreading.",
                    metadata={"x": mx, "y": my}
                )
            elif d["type"] == "ACID_RAIN":
                for _ in range(5):
                    rx = self.random.randint(0, self.spatial_map.width - 1)
                    ry = self.random.randint(0, self.spatial_map.height - 1)
                    self.spatial_map.food_nodes[rx, ry] = max(0.0, self.spatial_map.food_nodes[rx, ry] - 1.0)
                    self.spatial_map.wood_nodes[rx, ry] = max(0.0, self.spatial_map.wood_nodes[rx, ry] - 1.0)
                for agent in self.schedule.agents:
                    if isinstance(agent, CitizenAgent) and self.random.random() < 0.2:
                        agent.health -= 5.0
                        agent.death_cause = "Acid Rain Corrosion"
            
            if d["ticks_remaining"] > 0:
                surviving_disasters.append(d)
        self.active_disasters = surviving_disasters

        extinguished = []
        new_fires = {}
        for (fx, fy), ticks in list(self.burning_cells.items()):
            new_ticks = ticks - 1
            if new_ticks <= 0:
                extinguished.append((fx, fy))
            else:
                self.burning_cells[(fx, fy)] = new_ticks
                for a in self.grid.get_cell_list_contents((fx, fy)):
                    if isinstance(a, CitizenAgent):
                        a.health -= 15.0
                        a.is_burning = True
                        a.death_cause = "Immolation"
                if self.random.random() < 0.15:
                    adj = self.grid.get_neighborhood((fx, fy), moore=True, include_center=False)
                    target_cell = self.random.choice(adj)
                    terrain_type = self.spatial_map.terrain[target_cell[0], target_cell[1]]
                    if terrain_type in [1, 2] and target_cell not in self.burning_cells:
                        new_fires[target_cell] = 5
                        
        for ext in extinguished:
            del self.burning_cells[ext]
            
        for fc, duration in new_fires.items():
            self.burning_cells[fc] = duration

        sick_citizens = [a for a in self.schedule.agents if isinstance(a, CitizenAgent) and a.is_sick]
        for sick in sick_citizens:
            sick.sickness_level += 5.0
            sick.health -= 5.0
            sick.death_cause = "Virus Infection"
            
            if sick.sickness_level > 30.0:
                adj_agents = self.grid.get_neighbors(sick.pos, moore=True, include_center=False)
                for other in adj_agents:
                    if isinstance(other, CitizenAgent) and not other.is_sick:
                        if self.random.random() < 0.25:
                            other.is_sick = True
                            other.sickness_level = 10.0
                            event_bus.publish(
                                "INFECTED",
                                self.world_id,
                                self.tick_counter,
                                source_id=other.unique_id,
                                description=f"{other.name} got infected by {sick.name}.",
                                metadata={"infected_by": sick.unique_id}
                            )

    def extinguish_fire(self, coord: tuple):
        if coord in self.burning_cells:
            del self.burning_cells[coord]
            event_bus.publish(
                "FIRE_EXTINGUISHED",
                self.world_id,
                self.tick_counter,
                description=f"Fire at {coord} was extinguished.",
                metadata={"coords": coord}
            )

    def get_active_disasters_near(self, pos: tuple) -> List[Dict[str, Any]]:
        near = []
        for d in self.active_disasters:
            dist = ((d["x"] - pos[0])**2 + (d["y"] - pos[1])**2)**0.5
            if dist < 8:
                near.append(d)
        for fx, fy in self.burning_cells:
            dist = ((fx - pos[0])**2 + (fy - pos[1])**2)**0.5
            if dist < 5:
                near.append({"type": "FIRE", "x": fx, "y": fy})
        return near

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
