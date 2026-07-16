import os
import shutil
import tempfile
import pytest
from backend.app.core.engine import CivilizationEngine, CitizenAgent
from backend.app.simulation.economy import MarketBook, Order
from backend.app.agents.memory import MemoryStore
from backend.app.agents.values import CitizenValues
from backend.app.agents.needs import CitizenNeeds
from backend.app.utils.serialization import save_world, load_world
from backend.app.database import init_databases

@pytest.fixture(scope="session", autouse=True)
def init_db():
    init_databases()

def test_engine_init_and_tick():
    # Test simulation model creation and state progressions
    engine = CivilizationEngine(
        world_id="test-world-uuid",
        name="Test Faction",
        seed=42,
        width=10,
        height=10
    )
    assert engine.tick_counter == 0
    assert len(engine.schedule.agents) == 0
    
    # Add a citizen
    agent = engine.add_citizen("Test Agent", age=25, wealth=50.0, pos=(5, 5))
    assert len(engine.schedule.agents) == 1
    assert agent.pos == (5, 5)
    
    # Execute a step
    engine.step()
    assert engine.tick_counter == 1
    assert agent.age > 25

def test_economy_orders_matching():
    # Test supply and demand matching engine
    market = MarketBook(market_id="m1", name="Plaza")
    
    # Buy bid
    bid = Order(agent_id="buyer", resource_type="food", quantity=2.0, price=3.0, order_type="BID")
    # Sell ask
    ask = Order(agent_id="seller", resource_type="food", quantity=2.0, price=2.0, order_type="ASK")
    
    market.submit_order(bid)
    market.submit_order(ask)
    
    # Matching should clear quantity and discover mid price 2.5
    assert len(market.bids["food"]) == 0
    assert len(market.asks["food"]) == 0
    assert market.prices["food"] != 1.0 # Base price adjusted

def test_agent_memory_and_decay():
    # Test priority decay metrics
    store = MemoryStore(agent_id="agent-1")
    
    store.add_memory("Discovered an iron deposit in the north hills.", importance=8.0, current_tick=10)
    store.add_memory("Had a pleasant chat with a neighbor.", importance=3.0, current_tick=20)
    
    # Query memories at tick 50 (decay active)
    results = store.query_memories("iron", current_tick=50, limit=1)
    assert len(results) == 1
    assert "iron deposit" in results[0]

def test_world_serialization():
    # Create temp directory for snapshot Parquet files
    temp_dir = tempfile.mkdtemp()
    try:
        engine = CivilizationEngine(
            world_id="serialization-test",
            name="Ser World",
            seed=101,
            width=8,
            height=8
        )
        engine.add_citizen("John Doe", age=30, wealth=20.0, pos=(2, 2))
        engine.step()
        
        # Save snapshot
        save_world(engine, temp_dir)
        
        # Load snapshot
        new_engine = load_world(temp_dir)
        assert new_engine.world_id == "serialization-test"
        assert new_engine.tick_counter == 1
        assert len(new_engine.schedule.agents) == 1
        
        loaded_agent = new_engine.schedule.agents[0]
        assert loaded_agent.name == "John Doe"
        assert loaded_agent.pos == (2, 2)
        
    finally:
        shutil.rmtree(temp_dir)
