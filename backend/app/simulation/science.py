import random
from typing import Dict, List
from backend.app.core.event_bus import event_bus

class ScienceEngine:
    """Manages tech tree research, discoveries, and language/cultural evolution shifts"""
    def __init__(self, world_id: str):
        self.world_id = world_id
        # Technology list: Name -> {"cost": points, "progress": points, "discovered": bool, "modifiers": dict}
        self.techs: Dict[str, Dict] = {
            "Agriculture": {"cost": 50, "progress": 0, "discovered": False, "modifier": "food_multiplier"},
            "Metallurgy": {"cost": 100, "progress": 0, "discovered": False, "modifier": "iron_multiplier"},
            "Electricity": {"cost": 250, "progress": 0, "discovered": False, "modifier": "wood_efficiency"},
            "Automation": {"cost": 500, "progress": 0, "discovered": False, "modifier": "production_boost"}
        }
        
        # Cultural dialects representations
        self.global_culture = {"tradition": 0.5, "science": 0.5, "art": 0.5}
        self.dialects: Dict[str, str] = {"faction_alpha": "Standard", "faction_beta": "Standard"}

    def contribute_research(self, amount: float, tick: int):
        """Allocate research points from citizens' work to discover new technologies"""
        undiscovered = [name for name, t in self.techs.items() if not t["discovered"]]
        if not undiscovered:
            return

        # Allocate points to first undiscovered tech
        target_tech = undiscovered[0]
        self.techs[target_tech]["progress"] += amount
        
        if self.techs[target_tech]["progress"] >= self.techs[target_tech]["cost"]:
            self.techs[target_tech]["discovered"] = True
            
            event_bus.publish(
                "TECH_DISCOVERED",
                self.world_id,
                tick,
                description=f"Scientific breakthrough! '{target_tech}' has been discovered.",
                metadata={"tech": target_tech}
            )

    def tick_cultural_drift(self, tick: int):
        """Gradually evolve dialects and cultural coefficients randomly"""
        self.global_culture["tradition"] += random.uniform(-0.01, 0.01)
        self.global_culture["science"] += random.uniform(-0.01, 0.01)
        self.global_culture["art"] += random.uniform(-0.01, 0.01)
        
        # Enforce boundary checks
        for key in self.global_culture:
            self.global_culture[key] = max(0.0, min(1.0, self.global_culture[key]))
            
        # Example dialect shift
        if random.random() < 0.05:
            # Words drift slightly
            event_bus.publish(
                "DIALECT_DRIFT",
                self.world_id,
                tick,
                description="Language dialect drift observed. New words and accents are emerging.",
                metadata={"culture_coefficients": self.global_culture}
            )
        
    def get_discovery_modifiers(self) -> Dict[str, float]:
        """Returns active modifiers to adjust resource yields in simulation core"""
        modifiers = {"food_multiplier": 1.0, "iron_multiplier": 1.0, "wood_efficiency": 1.0, "production_boost": 1.0}
        for name, t in self.techs.items():
            if t["discovered"]:
                modifiers[t["modifier"]] = 1.5 # 50% yield bonus
        return modifiers
