import pytest
import asyncio
from app.bus.core import bus
from app.bus.handlers import register_all_handlers
from app.engine.twin import TwinState, MatchPhase, DEFAULT_SCENARIO
from app.engine.prediction import prediction_engine
from app.engine.decision import decision_engine
from app.models import Incident, Prediction, Recommendation, Decision

@pytest.mark.asyncio
async def test_event_bus_handlers():
    # Verify event handlers can be registered and start up cleanly
    register_all_handlers(bus)
    assert len(bus._handlers) > 0


def test_twin_state_initialization(db):
    state = TwinState(DEFAULT_SCENARIO)
    assert state.tick == 0
    assert state.match_phase == MatchPhase.PRE_MATCH
    assert len(state.sector_counts) > 0
    assert len(state.vehicles) > 0


@pytest.mark.asyncio
async def test_prediction_engine_processing(db):
    # Verify prediction engine can register to event bus
    prediction_engine.register_listeners(bus)
    assert len(prediction_engine.listeners) > 0


@pytest.mark.asyncio
async def test_decision_engine_rules(db):
    # Verify decision engine listeners can bind
    decision_engine.register_listeners(bus)
    assert len(decision_engine.listeners) > 0
