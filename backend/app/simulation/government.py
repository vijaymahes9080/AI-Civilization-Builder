import random
from typing import List, Dict, Any
from backend.app.core.event_bus import event_bus

class GovernmentEngine:
    """Manages political opinions, voting behavior, tax cycles, and regime updates"""
    def __init__(self, world_id: str, regime_type: str = "DEMOCRACY"):
        self.world_id = world_id
        self.regime_type = regime_type
        self.tax_rate = 0.1
        self.treasury = 50.0
        self.stability = 1.0

    def trigger_voting_cycle(self, citizens: List[Any], tick: int):
        """Simulate a civic proposal cycle where citizens vote on tax rate adjustments"""
        if not citizens:
            return

        # Citizens vote for higher/lower taxes depending on their Agreeableness (welfare preference)
        # and current wealth (self-interest)
        votes_increase = 0
        votes_decrease = 0

        for agent in citizens:
            vote_score = agent.personality["a"] * 0.6 - (agent.wealth / 100.0) * 0.4
            if vote_score > 0.1:
                votes_increase += 1
            else:
                votes_decrease += 1

        old_rate = self.tax_rate
        if votes_increase > votes_decrease:
            self.tax_rate = min(0.4, self.tax_rate + 0.02)
        else:
            self.tax_rate = max(0.0, self.tax_rate - 0.02)

        if self.tax_rate != old_rate:
            event_bus.publish(
                "LAW_AMENDED",
                self.world_id,
                tick,
                description=f"Tax rate amended by democratic vote. New tax rate: {self.tax_rate * 100:.1f}%.",
                metadata={"votes_for_increase": votes_increase, "votes_for_decrease": votes_decrease, "tax_rate": self.tax_rate}
            )

    def collect_taxes(self, citizens: List[Any], tick: int):
        """Deducts taxes from citizens and deposits into the public treasury"""
        total_collected = 0.0
        for agent in citizens:
            tax = agent.wealth * self.tax_rate
            agent.wealth -= tax
            total_collected += tax
            
        self.treasury += total_collected
        
        event_bus.publish(
            "TAX_COLLECTED",
            self.world_id,
            tick,
            description=f"Collected {total_collected:.2f} wealth in public taxes. Treasury: {self.treasury:.2f}.",
            metadata={"amount": total_collected, "treasury": self.treasury}
        )
