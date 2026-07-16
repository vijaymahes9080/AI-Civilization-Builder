import networkx as nx
from typing import Dict, Any
from backend.app.core.event_bus import event_bus

class DiplomacyEngine:
    """Manages international treaties, border agreements, and conflict/alliance graphs"""
    def __init__(self, world_id: str):
        self.world_id = world_id
        # Relationship graph: nodes are factions/settlements, edges hold trust/alliance attributes
        self.relations = nx.Graph()

    def add_faction(self, faction_name: str):
        self.relations.add_node(faction_name, wealth=100.0, power=50.0)

    def set_relationship(self, faction_a: str, faction_b: str, trust_score: float, status: str = "NEUTRAL"):
        """Set alignment values between two factions: ALLIED, NEUTRAL, HOSTILE"""
        self.relations.add_edge(faction_a, faction_b, trust=trust_score, status=status)
        
        event_bus.publish(
            "DIPLOMATIC_SHIFT",
            self.world_id,
            tick=0,
            description=f"Diplomatic relation between {faction_a} and {faction_b} shifted to {status}.",
            metadata={"faction_a": faction_a, "faction_b": faction_b, "trust": trust_score, "status": status}
        )

    def run_diplomatic_decay(self, tick: int):
        """Gradually normalize hostile/friendly relations over time unless reinforced"""
        for u, v, d in self.relations.edges(data=True):
            current_trust = d.get("trust", 0.5)
            # Drift towards 0.5 (neutrality)
            d["trust"] = current_trust * 0.98 + 0.5 * 0.02
            
            # If trust falls extremely low, shift status to hostile
            if d["trust"] < 0.2 and d["status"] != "HOSTILE":
                d["status"] = "HOSTILE"
                event_bus.publish(
                    "DIPLOMATIC_WAR",
                    self.world_id,
                    tick,
                    description=f"Relations collapsed! {u} and {v} are now HOSTILE.",
                    metadata={"faction_a": u, "faction_b": v}
                )
