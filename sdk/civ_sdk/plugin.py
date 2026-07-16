from typing import Any, Dict

class BasePlugin:
    """Base class for all AI Civilization Builder mods and extensions"""
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def on_simulation_start(self, engine: Any):
        """Hook called when the simulation environment is initialized"""
        pass

    def on_tick_end(self, engine: Any, current_tick: int):
        """Hook called after every simulation tick"""
        pass

class EconomyModifierPlugin(BasePlugin):
    """SDK template class to override market price shifts and trade rules"""
    def __init__(self, name: str, version: str, price_coefficient: float):
        super().__init__(name, version)
        self.price_coefficient = price_coefficient

    def modify_clearing_price(self, resource: str, current_price: float) -> float:
        """Apply custom multiplier to commodity base prices"""
        if resource == "iron":
            return current_price * self.price_coefficient
        return current_price

class AgentBehaviorPlugin(BasePlugin):
    """SDK template class to adjust AI citizen goals and decision rules"""
    def __init__(self, name: str, version: str):
        super().__init__(name, version)

    def select_next_behavior(self, agent: Any, environment: Dict[str, Any]) -> str:
        """Inject new choice routing to agent state actions"""
        # Return behavior choice override
        return "FORAGE"
