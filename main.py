from src.data_loader import clean_and_aggregate, get_sku_weights, load_salidas
from src.inventory_engine import InventoryOptimizer
from src.routing_optimizer import RoutingOptimizer
import pandas as pd
import numpy as np

def main():
    print("🚀 Iniciando SupplyChain-OptiFlow con datos REV...")

    # 1. Cargar y procesar datos
    demand_data = clean_and_aggregate()
    sku_weights = get_sku_weights()
    df_salidas = load_salidas()

    print("✅ Datos cargados correctamente.")

    # 2. Calcular KPIs de inventario por categoría
    resultados = []
    for cat, data in demand_data.items():
        opt = InventoryOptimizer(
            demand_mean=data["mean"],
            demand_std=data["std"],
            lead_time_mean=7,
            lead_time_std=2,
            unit_cost=10,          # valor promedio, se puede ajustar
            holding_cost_pct=0.1,
            order_cost=50,
            stockout_cost=20
        )
        kpis = opt.compute_kpis(annual_demand=data["mean"] * 365)
        resultados.append({
            "Categoría": cat,
            "Demanda Promedio Diaria": data["mean"],
            "EOQ": kpis["EOQ"],
            "Punto de Reorden": kpis["Reorder Point"],
            "Stock Seguridad": kpis["Safety Stock"],
            "Costo Total Anual": kpis["Total Annual Cost"]
        })
    df_resultados = pd.DataFrame(resultados)
    df_resultados.to_csv("data/outputs/inventory_kpis.csv", index=False)
    print("📊 KPIs de inventario guardados.")

    # 3. Optimización de rutas (ejemplo con los primeros 10 clientes)
    clientes = df_salidas["NOMBRE DE CLIENTE"].dropna().unique().tolist()
    if len(clientes) >= 2:
        # Simular ubicaciones (en un caso real se geocodificarían)
        n_nodes = min(10, len(clientes))
        locations = [(19.4 + np.random.randn()*0.5, -99.1 + np.random.randn()*0.5) for _ in range(n_nodes)]
        demands = [0] + [np.random.randint(1, 20) for _ in range(n_nodes-1)]
        capacities = [100, 100, 100]
        # Matriz de distancias simulada
        dist = np.random.randint(10, 100, (n_nodes, n_nodes))
        np.fill_diagonal(dist, 0)
        dist_sym = (dist + dist.T) // 2
        routing = RoutingOptimizer(
            locations=locations,
            demands=demands,
            vehicle_capacities=capacities,
            distance_matrix=dist_sym.tolist()
        )
        routes = routing.solve()
        if routes:
            print("✅ Rutas optimizadas:")
            for i, route in enumerate(routes):
                print(f"   Vehículo {i+1}: {route}")
        else:
            print("❌ No se encontró solución de ruteo.")
    else:
        print("⚠️ No hay suficientes clientes para optimizar rutas.")

    print("✅ Proceso completado.")

if __name__ == "__main__":
    main()
