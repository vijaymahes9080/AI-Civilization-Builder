import json
import httpx
from typing import Dict, List, Any
from backend.app.config import settings
from backend.app.agents.memory import MemoryStore
from backend.app.agents.values import CitizenValues
from backend.app.agents.needs import CitizenNeeds

class CitizenBrain:
    """
    Cognitive reasoning pipeline for AI Citizens. 
    Handles prompt building, memory lookup, local Ollama LLM calling, and decision-making fallback.
    """
    def __init__(self, agent_id: str, name: str, values: CitizenValues, needs: CitizenNeeds):
        self.agent_id = agent_id
        self.name = name
        self.values = values
        self.needs = needs
        self.memory_store = MemoryStore(agent_id)
        
        # Local model endpoint URL
        self.ollama_endpoint = f"{settings.OLLAMA_URL}/api/generate"

    async def decide_action(self, tick: int, environmental_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gathers memory, details personal state, calls local Ollama for next plan step, 
        or triggers rule heuristics as fallback.
        """
        # 1. Memory query
        query_key = f"What should I do? Needs: {self.needs.get_needs_summary()}"
        relevant_memories = self.memory_store.query_memories(query_key, tick, limit=4)
        
        # 2. Build prompt context
        prompt_content = self._build_prompt_payload(tick, environmental_context, relevant_memories)
        
        # 3. Call local LLM
        decision = await self._call_local_llm(prompt_content)
        
        # 4. If LLM failed, build basic default decision
        if not decision:
            decision = self._get_heuristic_fallback_decision(environmental_context)
            
        # 5. Save memory of decision
        action_desc = decision.get("action_description", "continued basic tasks")
        self.memory_store.add_memory(
            f"Decided to: {action_desc}. Reason: {decision.get('explanation', 'Heuristic routing')}",
            importance=5.0,
            current_tick=tick
        )
        
        return decision

    def _build_prompt_payload(self, tick: int, env: Dict[str, Any], memories: List[str]) -> str:
        persona = self.values.generate_persona_description()
        needs_summary = self.needs.get_needs_summary()
        
        memories_str = "\n".join([f"- {m}" for m in memories]) if memories else "No relevant memories."
        
        prompt = f"""
System: You are an autonomous citizen agent named '{self.name}' living in a persistent civilization builder simulation.
Persona: {persona}
Current Status:
- Tick: {tick}
- Needs (0-100 scale): {json.dumps(needs_summary)}
- Inventory: {json.dumps(env.get('inventory', {}))}
- Nearby Citizens: {json.dumps(env.get('nearby_citizens', []))}
- Climate/Weather: {env.get('weather', 'Sunny')}, Temp: {env.get('temperature', 20)}C
- Surrounding cells: {json.dumps(env.get('cells', []))}

Recent Memories:
{memories_str}

Decide your next action and explain the rationale. 
Return your response ONLY as a valid JSON object matching this schema:
{{
  "action_type": "MOVE" | "FORAGE" | "TRADE" | "REST" | "TALK",
  "target_coordinate": [x, y],
  "speech_content": "optional dialogue text if action is TALK",
  "action_description": "short description of your action",
  "explanation": "Why did you choose this? State reasoning, goals, trust scores, and expectations."
}}
"""
        return prompt

    async def _call_local_llm(self, prompt: str) -> Dict[str, Any]:
        """Queries local Ollama instance with timeout and returns parsed JSON output"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ollama_endpoint,
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,
                            "num_predict": 150
                        }
                    },
                    timeout=2.5 # Short timeout so simulation ticks aren't blocked
                )
                if response.status_code == 200:
                    text_out = response.json().get("response", "").strip()
                    # Extract JSON block
                    start = text_out.find("{")
                    end = text_out.rfind("}") + 1
                    if start != -1 and end != -1:
                        return json.loads(text_out[start:end])
        except Exception:
            pass  # Fallback gracefully
        return {}

    def _get_heuristic_fallback_decision(self, env: Dict[str, Any]) -> Dict[str, Any]:
        """Provides instant fallback if LLM is offline or times out"""
        needs = self.needs.get_needs_summary()
        if needs["hunger"] > 60:
            return {
                "action_type": "FORAGE",
                "action_description": "Forage food resources",
                "explanation": "Hunger is high, fall back to search food."
            }
        return {
            "action_type": "MOVE",
            "action_description": "Explore the region",
            "explanation": "Exploring nearby terrain to locate resources."
        }
