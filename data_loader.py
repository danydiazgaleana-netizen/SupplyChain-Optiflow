import pandas as pd
import numpy as np
from pathlib import Path

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")

def load_proyeccion():
    """Carga la hoja de proyección de ventas por categoría y canal."""
    file = DATA_RAW / "Proyección 25-29 - Almacén.xlsx"
    # Hoja "Resumen de Proyección pzs 24-29"
    df_resumen = pd.read_excel(file, sheet_name="Resumen de Proyección pzs 24-29", header=1)
    # Hoja "Proyección Almacén 25-29" (ventas por canal)
    df_canales = pd.read_excel(file, sheet_name="Proyección Almacén 25-29", header=2)
    return df_resumen, df_canales

def load_cajas():
    """Carga medidas de cajas y pesos por SKU."""
    file = DATA_RAW / "MEDIDAS CAJAS REV OK.xlsx"
    # Hoja "LISTA CAJAS"
    df_cajas = pd.read_excel(file, sheet_name="LISTA CAJAS")
    # Hoja "NIGHTMARE" (pesos por SKU)
    df_pesos = pd.read_excel(file, sheet_name="NIGHTMARE")
    return df_cajas, df_pesos

def load_salidas():
    """Carga histórico de salidas a clientes."""
    file = DATA_RAW / "Fechas de Salidas CEDIS.xlsx"
    df_salidas = pd.read_excel(file, sheet_name="CEDIS")
    df_salidas["SALIDA DE EMBARQUE"] = pd.to_datetime(df_salidas["SALIDA DE EMBARQUE"])
    df_salidas["FECHA DE CITA"] = pd.to_datetime(df_salidas["FECHA DE CITA"])
    return df_salidas

def clean_and_aggregate():
    """Limpia y agrega datos para el motor de optimización."""
    # Proyecciones por categoría (promedio anual)
    df_res, _ = load_proyeccion()
    # Tomamos las columnas de 2024-2029
    years = [2024, 2025, 2026, 2027, 2028, 2029]
    categories = df_res.iloc[1:6, 0].values  # Máscaras, Decorativos, Disfraces, Accesorios, Maquillajes
    demand_data = {}
    for i, cat in enumerate(categories):
        row = df_res.iloc[i+1, 1:7].values.astype(float)
        demand_data[cat] = {
            "annual_demand": row,
            "mean": np.mean(row),
            "std": np.std(row),
            "growth_rate": (row[-1] / row[0]) ** (1/5) - 1
        }
    return demand_data

def get_sku_weights():
    """Obtiene peso unitario por SKU desde la hoja NIGHTMARE."""
    _, df_pesos = load_cajas()
    sku_weight = df_pesos[["CLAVE", "PESO UNITARIO MASCARA KG."]].dropna()
    sku_weight = sku_weight.set_index("CLAVE").to_dict()["PESO UNITARIO MASCARA KG."]
    return sku_weight

if __name__ == "__main__":
    # Prueba de carga
    print("Cargando datos...")
    demand = clean_and_aggregate()
    print(f"Categorías cargadas: {list(demand.keys())}")
    print("Pesos de SKU (muestra):", dict(list(get_sku_weights().items())[:5]))