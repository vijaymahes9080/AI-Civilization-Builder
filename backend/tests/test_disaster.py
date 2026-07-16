"""
Disaster system unit tests for AI Civilization Builder.
Uses mocking to bypass sentence-transformers/Ollama so tests run fast.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.core.engine import CivilizationEngine, CitizenAgent
from backend.app.database import init_databases

# ─────────────────────────────────────────────────────────────────────────────
# Session-level DB init
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_databases()

# ─────────────────────────────────────────────────────────────────────────────
# Fixture: a fast engine with brain mocked out
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture
def make_engine():
    """
    Factory fixture. Returns a CivilizationEngine with CitizenBrain mocked so
    sentence-transformers never loads (fast tests).
    """
    def _factory(world_id, width=10, height=10, seed=42):
        with patch("backend.app.agents.brain.CitizenBrain", autospec=True) as MockBrain:
            MockBrain.return_value.decide_action = AsyncMock(
                return_value={"action": "IDLE", "reason": "mocked"}
            )
            engine = CivilizationEngine(
                world_id=world_id,
                name=world_id,
                seed=seed,
                width=width,
                height=height
            )
        # Patch all future brain.decide_action calls on existing agents
        for agent in engine.schedule.agents:
            agent.brain.decide_action = AsyncMock(return_value={"action": "IDLE", "reason": "mocked"})
        return engine
    return _factory


def _patch_agent_brain(agent):
    """Patch a single agent's brain so it never calls LLM."""
    agent.brain.decide_action = AsyncMock(return_value={"action": "IDLE", "reason": "mocked"})


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Meteor strike creates fire and damages agents
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_meteor_impact_and_fire():
    engine = CivilizationEngine(
        world_id="test-meteor-world",
        name="Meteor World",
        seed=101,
        width=10,
        height=10
    )

    # Place citizen at (5, 5) and mock its brain
    agent = engine.add_citizen("Survivor", age=25, wealth=100.0, pos=(5, 5))
    _patch_agent_brain(agent)

    # Summon meteor at (5, 5) — ticks_remaining=3
    engine.summon_disaster("METEOR", 5, 5)
    assert len(engine.active_disasters) == 1
    assert engine.active_disasters[0]["type"] == "METEOR"

    # Tick 3 times — meteor impacts exactly at tick 3 (ticks_remaining -> 0)
    await engine.step()
    await engine.step()
    await engine.step()

    # Disaster list must be empty after impact
    assert len(engine.active_disasters) == 0
    # Tile (5,5) must be on fire
    assert (5, 5) in engine.burning_cells
    # Agent took 50 hp blast damage
    assert agent.health < 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Epidemic infects patient-zero and spreads to nearby citizens
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_epidemic_transmission():
    engine = CivilizationEngine(
        world_id="test-virus-world",
        name="Virus World",
        seed=42,               # deterministic RNG
        width=10,
        height=10
    )

    # Two citizens on adjacent tiles so grid.get_neighbors picks them up
    patient_zero = engine.add_citizen("Zero", age=30, wealth=20.0, pos=(5, 5))
    healthy_one  = engine.add_citizen("Healthy", age=32, wealth=20.0, pos=(5, 6))
    _patch_agent_brain(patient_zero)
    _patch_agent_brain(healthy_one)

    # Infect patient zero
    engine.summon_disaster("EPIDEMIC", 5, 5)
    assert patient_zero.is_sick, "patient_zero should be sick immediately"

    # Tick enough to: (1) sickness_level reach 30, (2) spread rolls succeed.
    # sickness_level starts at 20, +5/tick → reaches >30 after 3 ticks.
    # We run 10 ticks with deterministic seed=42 to guarantee spread.
    for _ in range(10):
        await engine.step()

    # Either healthy_one got the virus OR took 5 hp/tick health damage from
    # being sick himself (health < 100 confirms infection occurred).
    assert healthy_one.is_sick or healthy_one.health < 100.0, (
        f"Expected healthy_one to be sick or damaged; "
        f"is_sick={healthy_one.is_sick}, health={healthy_one.health}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Acid Rain degrades crop tiles
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_acid_rain_degrades_resources():
    engine = CivilizationEngine(
        world_id="test-acid-world",
        name="Acid World",
        seed=77,
        width=10,
        height=10
    )

    total_food_before = float(engine.spatial_map.food_nodes.sum())
    engine.summon_disaster("ACID_RAIN", 5, 5)
    assert any(d["type"] == "ACID_RAIN" for d in engine.active_disasters)

    # Run for a few ticks to trigger resource erosion
    for _ in range(3):
        await engine.step()

    total_food_after = float(engine.spatial_map.food_nodes.sum())
    assert total_food_after < total_food_before, (
        "Acid Rain should have eroded food resources"
    )
