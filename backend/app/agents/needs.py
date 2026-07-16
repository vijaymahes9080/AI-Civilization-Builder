from typing import Dict

class CitizenNeeds:
    """Manages physiological and psychological needs for AI Citizens"""
    def __init__(self):
        self.hunger = 0.0         # 0 (full) to 100 (starving)
        self.exhaustion = 0.0     # 0 (rested) to 100 (exhausted)
        self.social_need = 0.0    # 0 (connected) to 100 (lonely)
        self.safety_need = 0.0    # 0 (safe) to 100 (scared)
        self.fulfillment = 50.0   # 0 (depressed) to 100 (happy/fulfilled)

    def update_needs(self, is_sheltered: bool, nearby_citizens: int):
        """Simulate change in needs during a tick"""
        # Hunger progresses
        self.hunger = min(100.0, self.hunger + 4.0)
        
        # Exhaustion progresses
        self.exhaustion = min(100.0, self.exhaustion + 3.0)
        
        # Social need ticks up if lonely, ticks down if nearby citizens
        if nearby_citizens > 0:
            self.social_need = max(0.0, self.social_need - 8.0)
        else:
            self.social_need = min(100.0, self.social_need + 2.0)
            
        # Safety decays without shelter
        if not is_sheltered:
            self.safety_need = min(100.0, self.safety_need + 5.0)
        else:
            self.safety_need = max(0.0, self.safety_need - 10.0)

        # Recalculate fulfillment score based on overall needs
        stress_factors = (self.hunger + self.exhaustion + self.social_need + self.safety_need) / 4.0
        self.fulfillment = max(0.0, min(100.0, 100.0 - stress_factors))

    def get_needs_summary(self) -> Dict[str, float]:
        return {
            "hunger": self.hunger,
            "exhaustion": self.exhaustion,
            "social_need": self.social_need,
            "safety_need": self.safety_need,
            "fulfillment": self.fulfillment
        }
