import asyncio
from typing import Dict
from backend.app.core.engine import CivilizationEngine

class SimulationScheduler:
    """Manages persistent running tasks for multiple simulation worlds in the background"""
    def __init__(self):
        self.active_simulations: Dict[str, CivilizationEngine] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.tick_delays: Dict[str, float] = {}  # Delay in seconds per tick

    def register_world(self, world_id: str, engine: CivilizationEngine):
        self.active_simulations[world_id] = engine
        self.tick_delays[world_id] = 1.0  # Default 1.0 seconds

    def start(self, world_id: str):
        """Resume or start simulation loop in background"""
        if world_id not in self.active_simulations:
            raise ValueError(f"World {world_id} is not registered.")
        
        if world_id in self.running_tasks and not self.running_tasks[world_id].done():
            return  # Already running
            
        self.running_tasks[world_id] = asyncio.create_task(self._simulation_loop(world_id))

    def pause(self, world_id: str):
        """Stop simulation loop background task"""
        if world_id in self.running_tasks:
            self.running_tasks[world_id].cancel()
            del self.running_tasks[world_id]

    def set_speed(self, world_id: str, multiplier: float):
        """Alter speed of simulation (1x, 10x, 100x etc.) by shifting delay duration"""
        if world_id in self.active_simulations:
            # Base delay is 1.0 second. speed multiplier = 10 -> delay = 0.1s
            self.tick_delays[world_id] = max(0.001, 1.0 / multiplier)

    def step_once(self, world_id: str):
        """Manually execute a single tick"""
        if world_id in self.active_simulations:
            self.active_simulations[world_id].step()

    async def _simulation_loop(self, world_id: str):
        engine = self.active_simulations[world_id]
        try:
            while True:
                engine.step()
                delay = self.tick_delays.get(world_id, 1.0)
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass  # Task cancelled, exit loop clean

# Global Scheduler Singleton
scheduler = SimulationScheduler()
