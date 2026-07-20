import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import sys
sys.path.append('../src')
from data_loader import clean_and_aggregate, get_sku_weights
from inventory_engine import InventoryOptimizer

st.set_page_config(layout="wide")
st.title("📦 SupplyChain-OptiFlow Dashboard")
st.markdown("### Optimización de Inventarios y Rutas con Datos REV")

# Cargar datos
demand_data = clean_and_aggregate()
sku_weights = get_sku_weights()

# Sidebar
st.sidebar.header("Configuración")
categoria = st.sidebar.selectbox("Selecciona categoría", list(demand_data.keys()))
service_level = st.sidebar.slider("Nivel de Servicio (%)", 80, 99, 95) / 100

# KPIs de la categoría
cat = demand_data[categoria]
mean_demand = cat["mean"]
std_demand = cat["std"]

# Parámetros de inventario (valores típicos, se pueden ajustar)
opt = InventoryOptimizer(
    demand_mean=mean_demand,
    demand_std=std_demand,
    lead_time_mean=7,
    lead_time_std=2,
    unit_cost=10,
    holding_cost_pct=0.1,
    order_cost=50,
    stockout_cost=20
)
kpis = opt.compute_kpis(annual_demand=mean_demand * 365)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Demanda Promedio Diaria", f"{mean_demand:.0f}")
col2.metric("EOQ", f"{kpis['EOQ']:.0f}")
col3.metric("Punto de Reorden", f"{kpis['Reorder Point']:.0f}")
col4.metric("Stock de Seguridad", f"{kpis['Safety Stock']:.0f}")

# Proyección de demanda
st.subheader(f"📈 Proyección de Demanda - {categoria}")
years = [2024, 2025, 2026, 2027, 2028, 2029]
values = [mean_demand * 365 * (1 + cat["growth_rate"])**i for i in range(6)]
df_proy = pd.DataFrame({"Año": years, "Demanda Anual": values})
fig = px.line(df_proy, x="Año", y="Demanda Anual", title=f"Proyección {categoria}")
st.plotly_chart(fig, use_container_width=True)

# Simulación de demanda
if st.button("Simular demanda para 30 días"):
    sim_df = opt.simulate_demand(n_simulations=100, horizon=30)
    fig_sim = px.line(sim_df.T, title="Simulación de Demanda (30 días)")
    st.plotly_chart(fig_sim)

# Mapa de rutas (ejemplo con ubicaciones simuladas)
st.subheader("🗺️ Ruteo de Entregas")
# Usamos datos de salidas reales para generar direcciones de clientes
# (simplificado: tomamos nombres de clientes de Fechas de Salidas)
from data_loader import load_salidas
df_salidas = load_salidas()
clientes = df_salidas["NOMBRE DE CLIENTE"].dropna().unique().tolist()[:10]

# Crear ubicaciones dummy (en la práctica se geocodificarían)
m = folium.Map(location=[19.4326, -99.1332], zoom_start=5)
for cliente in clientes:
    lat = 19.4 + np.random.randn() * 0.5
    lon = -99.1 + np.random.randn() * 0.5
    folium.Marker([lat, lon], popup=cliente).add_to(m)
folium.Marker([19.4326, -99.1332], popup="CEDIS", icon=folium.Icon(color="red")).add_to(m)
st_folium(m, width=700, height=500)

# Mostrar tabla de KPIs por SKU (opcional)
st.subheader("📊 KPIs de Inventario por SKU (muestra)")
if st.checkbox("Mostrar KPIs de SKUs"):
    sku_sample = list(sku_weights.keys())[:10]
    data_skus = []
    for sku in sku_sample:
        weight = sku_weights.get(sku, 0)
        opt_sku = InventoryOptimizer(
            demand_mean=mean_demand * 0.1,  # simplificado
            demand_std=std_demand * 0.1,
            lead_time_mean=7,
            lead_time_std=2,
            unit_cost=10,
            holding_cost_pct=0.1,
            order_cost=50,
            stockout_cost=20
        )
        k = opt_sku.compute_kpis()
        data_skus.append({"SKU": sku, "Peso (kg)": weight, "EOQ": k["EOQ"], "Punto Reorden": k["Reorder Point"]})
    df_skus = pd.DataFrame(data_skus)
    st.dataframe(df_skus)