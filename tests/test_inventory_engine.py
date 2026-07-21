import pytest
import numpy as np
from src.inventory_engine import InventoryOptimizer

@pytest.fixture
def optimizer():
    return InventoryOptimizer(
        demand_mean=100,
        demand_std=20,
        lead_time_mean=7,
        lead_time_std=2,
        unit_cost=10,
        holding_cost_pct=0.1,
        order_cost=50,
        stockout_cost=20
    )

def test_eoq_positive(optimizer):
    assert optimizer.eoq() > 0

def test_safety_stock_non_negative(optimizer):
    assert optimizer.safety_stock() >= 0

def test_reorder_point_positive(optimizer):
    assert optimizer.reorder_point() > 0

def test_total_cost_non_negative(optimizer):
    assert optimizer.total_cost(order_quantity=200) >= 0

def test_optimize_order_quantity(optimizer):
    q = optimizer.optimize_order_quantity()
    assert q > 0

def test_extreme_lead_time(optimizer):
    optimizer.lead_time_mean = 30
    assert optimizer.reorder_point() >= 0
