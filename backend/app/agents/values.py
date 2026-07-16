from typing import Dict

class CitizenValues:
    """Manages citizen DNA mutations, personality profiles, and ethics models"""
    def __init__(self, dna: str, personality: Dict[str, float]):
        self.dna = dna
        self.personality = personality  # {"o": float, "c": float, "e": float, "a": float, "n": float}
        self.ethics = self._derive_ethical_profile()

    def _derive_ethical_profile(self) -> Dict[str, float]:
        """Derive moral compass parameters from personality traits"""
        # Example ethics profile mapping:
        # High Agreeableness -> High altruism
        # High Conscientiousness -> High lawfulness/obedience
        # High Openness -> High progressivism
        return {
            "altruism": self.personality.get("a", 0.5) * 0.8 + 0.1,
            "lawfulness": self.personality.get("c", 0.5) * 0.7 + self.personality.get("a", 0.5) * 0.2,
            "progressivism": self.personality.get("o", 0.5) * 0.9,
            "individualism": 1.0 - self.personality.get("a", 0.5) * 0.6
        }

    def generate_persona_description(self) -> str:
        """Constructs an textual summary of the agent's inner workings for the LLM prompt context"""
        p = self.personality
        traits = []
        if p["o"] > 0.7: traits.append("inquisitive and highly creative")
        if p["c"] > 0.7: traits.append("extremely organized, reliable, and law-abiding")
        if p["e"] > 0.7: traits.append("highly extroverted, talkative, and social")
        if p["a"] > 0.7: traits.append("compassionate, empathetic, and cooperative")
        if p["n"] > 0.7: traits.append("anxious, reactive, and easily stressed")
        
        if p["o"] < 0.3: traits.append("traditional and practical")
        if p["c"] < 0.3: traits.append("spontaneous and disorganized")
        if p["e"] < 0.3: traits.append("introverted, quiet, and reserved")
        if p["a"] < 0.3: traits.append("competitive, analytical, and skeptical")
        if p["n"] < 0.3: traits.append("emotionally resilient and calm")

        traits_str = ", ".join(traits) if traits else "balanced and adaptable"
        return f"A citizen who is {traits_str}. DNA Profile: {self.dna}."
