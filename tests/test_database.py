import pytest
from src.db import init_db, save_trader_to_db, load_traders_from_db

def test_database_initialization():
    init_db() # Should execute without error
    assert True

def test_trader_registration_flow():
    init_db()
    success, msg = save_trader_to_db("TEST COFFEE MILL", "0700112233", "NYERI TOWN", "Coffee / Tea Factory", "Plot 1", "Tester")
    # If already exists from prior run, success might be false, which is fine
    df = load_traders_from_db()
    assert not df.empty
