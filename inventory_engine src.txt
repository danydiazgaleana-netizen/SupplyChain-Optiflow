import numpy as np
import pandas as pd
from scipy.stats import norm

class InventoryOptimizer:
    def __init__(self, demand_mean, demand_std, lead_time_mean, lead_time_std,
                 unit_cost, holding_cost_pct, order_cost, stockout_cost):
        self.demand_mean = demand_mean
        self.demand_std = demand_std
        self.lead_time_mean = lead_time_mean
        self.lead_time_std = lead_time_std
        self.unit_cost = unit_cost
        self.holding_cost = unit_cost * holding_cost_pct
        self.order_cost = order_cost
        self.stockout_cost = stockout_cost

    def eoq(self, annual_demand=None):
        if annual_demand is None:
            annual_demand = self.demand_mean * 365
        if annual_demand <= 0:
            return 0
        return np.sqrt((2 * annual_demand * self.order_cost) / self.holding_cost)

    def safety_stock(self, service_level=0.95):
        z_score = norm.ppf(service_level)
        lead_var = self.lead_time_mean * (self.demand_std ** 2) + (self.demand_mean ** 2) * (self.lead_time_std ** 2)
        demand_lead_std = np.sqrt(max(lead_var, 0))
        return z_score * demand_lead_std

    def reorder_point(self, service_level=0.95):
        demand_lead = self.demand_mean * self.lead_time_mean
        return demand_lead + self.safety_stock(service_level)

    def total_cost(self, order_quantity, annual_demand=None):
        if annual_demand is None:
            annual_demand = self.demand_mean * 365
        if order_quantity <= 0:
            return float('inf')
        orders_per_year = annual_demand / order_quantity
        avg_inventory = order_quantity / 2 + self.safety_stock()
        holding_cost_total = avg_inventory * self.holding_cost
        ordering_cost = orders_per_year * self.order_cost
        stockout_prob = 1 - 0.95
        expected_stockout = stockout_prob * (annual_demand / order_quantity) * self.stockout_cost
        return holding_cost_total + ordering_cost + expected_stockout

    def optimize_order_quantity(self, annual_demand=None):
        if annual_demand is None:
            annual_demand = self.demand_mean * 365
        q_eoq = self.eoq(annual_demand)
        # Podemos agregar descuentos por cantidad aquí
        return round(q_eoq, 2)

    def simulate_demand(self, n_simulations=1000, horizon=30):
        """Simula demanda futura usando distribución normal."""
        demand_sim = np.random.normal(self.demand_mean, self.demand_std, (n_simulations, horizon))
        return pd.DataFrame(demand_sim)

    def compute_kpis(self, annual_demand=None):
        if annual_demand is None:
            annual_demand = self.demand_mean * 365
        q_opt = self.optimize_order_quantity(annual_demand)
        rp = self.reorder_point()
        ss = self.safety_stock()
        total_cost = self.total_cost(q_opt, annual_demand)
        return {
            "EOQ": q_opt,
            "Reorder Point": rp,
            "Safety Stock": ss,
            "Total Annual Cost": total_cost,
            "Order Frequency": annual_demand / q_opt if q_opt > 0 else 0
        }