import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
RUTA_STOCK_TEORICO = "data/raw/stock_teorico.csv"
RUTA_CONTEO_FISICO = "data/raw/conteo_fisico_real.csv"
RUTA_DISCREPANCIAS = "data/outputs/discrepancias_inventario.csv"
RUTA_CLASIFICACION_ABC = "data/outputs/clasificacion_abc.csv"
RUTA_MERMAS = "data/outputs/mermas_inventario.csv"


class MotorConciliacion:
    """
    Componente B: Concilia inventario teórico vs. real.
    Detecta discrepancias, clasifica ABC y genera reportes de mermas.
    """

    def __init__(self):
        self.stock_teorico = None
        self.conteo_fisico = None
        self.df_conciliado = None

    def cargar_datos(self):
        """Carga los archivos de inventario teórico y conteo físico."""
        self.stock_teorico = self._cargar_stock_teorico()
        self.conteo_fisico = self._cargar_conteo_fisico()
        return self.stock_teorico, self.conteo_fisico

    def _cargar_stock_teorico(self) -> pd.DataFrame:
        """Carga stock teórico desde archivo CSV."""
        try:
            df = pd.read_csv(RUTA_STOCK_TEORICO)
            df['SKU'] = df['SKU'].astype(str).str.strip()
            df['Stock_Teorico'] = pd.to_numeric(df['Stock_Teorico'], errors='coerce').fillna(0)
            logger.info(f"📂 Stock teórico cargado: {len(df)} SKUs.")
            return df
        except FileNotFoundError:
            logger.warning(f"⚠️ Archivo no encontrado: {RUTA_STOCK_TEORICO}. Generando datos de ejemplo.")
            return self._generar_stock_ejemplo()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return pd.DataFrame()

    def _cargar_conteo_fisico(self) -> pd.DataFrame:
        """Carga conteo físico real desde archivo CSV."""
        try:
            df = pd.read_csv(RUTA_CONTEO_FISICO)
            df['SKU'] = df['SKU'].astype(str).str.strip()
            df['Stock_Fisico_Real'] = pd.to_numeric(df['Stock_Fisico_Real'], errors='coerce').fillna(0)
            logger.info(f"📂 Conteo físico cargado: {len(df)} SKUs.")
            return df
        except FileNotFoundError:
            logger.warning(f"⚠️ Archivo no encontrado: {RUTA_CONTEO_FISICO}. Generando datos de ejemplo.")
            return self._generar_conteo_ejemplo()
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return pd.DataFrame()

    def _generar_stock_ejemplo(self) -> pd.DataFrame:
        """Genera stock teórico de ejemplo."""
        skus = [
            {"SKU": "GLS-20001", "Stock_Teorico": 150, "Costo_Unitario": 45.5, "Demanda_Anual": 1200},
            {"SKU": "GLS-20002", "Stock_Teorico": 80, "Costo_Unitario": 78.2, "Demanda_Anual": 800},
            {"SKU": "GLS-20003", "Stock_Teorico": 200, "Costo_Unitario": 32.0, "Demanda_Anual": 2500},
            {"SKU": "GLS-20004", "Stock_Teorico": 45, "Costo_Unitario": 65.3, "Demanda_Anual": 450},
            {"SKU": "GLS-20009", "Stock_Teorico": 120, "Costo_Unitario": 89.9, "Demanda_Anual": 1800},
            {"SKU": "DEC-0101", "Stock_Teorico": 300, "Costo_Unitario": 15.5, "Demanda_Anual": 3200},
            {"SKU": "DEC-0102", "Stock_Teorico": 250, "Costo_Unitario": 12.3, "Demanda_Anual": 2800},
            {"SKU": "DIS-0101", "Stock_Teorico": 100, "Costo_Unitario": 45.0, "Demanda_Anual": 600},
            {"SKU": "ACC-0101", "Stock_Teorico": 500, "Costo_Unitario": 8.5, "Demanda_Anual": 5000},
            {"SKU": "MAQ-0101", "Stock_Teorico": 400, "Costo_Unitario": 5.2, "Demanda_Anual": 4500},
        ]
        df = pd.DataFrame(skus)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        df.to_csv(RUTA_STOCK_TEORICO, index=False)
        logger.info(f"📂 Stock teórico de ejemplo generado: {len(df)} SKUs.")
        return df

    def _generar_conteo_ejemplo(self) -> pd.DataFrame:
        """Genera conteo físico real con algunas discrepancias intencionales."""
        # Basado en stock teórico pero con variaciones
        skus = [
            {"SKU": "GLS-20001", "Stock_Fisico_Real": 142},  # -8
            {"SKU": "GLS-20002", "Stock_Fisico_Real": 85},   # +5
            {"SKU": "GLS-20003", "Stock_Fisico_Real": 195},  # -5
            {"SKU": "GLS-20004", "Stock_Fisico_Real": 48},   # +3
            {"SKU": "GLS-20009", "Stock_Fisico_Real": 110},  # -10 (merma)
            {"SKU": "DEC-0101", "Stock_Fisico_Real": 310},   # +10
            {"SKU": "DEC-0102", "Stock_Fisico_Real": 240},   # -10
            {"SKU": "DIS-0101", "Stock_Fisico_Real": 95},    # -5
            {"SKU": "ACC-0101", "Stock_Fisico_Real": 510},   # +10
            {"SKU": "MAQ-0101", "Stock_Fisico_Real": 395},   # -5
            # Agregar SKU que no está en stock teórico (fantasma)
            {"SKU": "GLS-99999", "Stock_Fisico_Real": 20},
        ]
        df = pd.DataFrame(skus)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        df.to_csv(RUTA_CONTEO_FISICO, index=False)
        logger.info(f"📂 Conteo físico de ejemplo generado: {len(df)} SKUs.")
        return df

    def conciliar(self) -> pd.DataFrame:
        """
        Concilia stock teórico vs. real.
        Retorna DataFrame con discrepancias calculadas.
        """
        if self.stock_teorico is None or self.conteo_fisico is None:
            self.cargar_datos()

        # Hacer merge de ambos DataFrames
        df = pd.merge(
            self.stock_teorico,
            self.conteo_fisico,
            on='SKU',
            how='outer'
        ).fillna(0)

        # Calcular discrepancias
        df['Stock_Teorico'] = df['Stock_Teorico'].fillna(0)
        df['Stock_Fisico_Real'] = df['Stock_Fisico_Real'].fillna(0)
        df['Discrepancia'] = df['Stock_Teorico'] - df['Stock_Fisico_Real']
        df['Discrepancia_Abs'] = df['Discrepancia'].abs()
        df['Porcentaje_Desviacion'] = np.where(
            df['Stock_Teorico'] > 0,
            (df['Discrepancia'] / df['Stock_Teorico']) * 100,
            0
        )

        # Identificar tipo de discrepancia
        df['Tipo_Discrepancia'] = df.apply(
            lambda row: 'Sobrante' if row['Discrepancia'] < 0 else ('Faltante' if row['Discrepancia'] > 0 else 'OK'),
            axis=1
        )

        # Si un SKU solo existe en físico, es un inventario fantasma
        df['Estado'] = df.apply(
            lambda row: 'Fantasma' if row['Stock_Teorico'] == 0 and row['Stock_Fisico_Real'] > 0 else 'Normal',
            axis=1
        )

        self.df_conciliado = df
        logger.info(f"✅ Conciliación completada: {len(df)} SKUs procesados.")
        return df

    def clasificar_abc(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Clasifica SKUs en A, B, C según demanda anual y valor de rotación.
        """
        if df is None:
            df = self.df_conciliado

        if df is None or df.empty:
            logger.warning("⚠️ No hay datos para clasificar ABC.")
            return pd.DataFrame()

        # Calcular valor de rotación = Demanda_Anual * Costo_Unitario
        df['Valor_Rotacion'] = df['Demanda_Anual'] * df['Costo_Unitario']

        # Ordenar por valor de rotación descendente
        df = df.sort_values('Valor_Rotacion', ascending=False)

        # Calcular porcentaje acumulado
        total_valor = df['Valor_Rotacion'].sum()
        df['Porcentaje_Acumulado'] = df['Valor_Rotacion'].cumsum() / total_valor * 100

        # Asignar categoría ABC
        df['Clasificacion_ABC'] = df['Porcentaje_Acumulado'].apply(
            lambda x: 'A' if x <= 70 else ('B' if x <= 90 else 'C')
        )

        # Agregar recomendación de ubicación
        df['Zona_Recomendada'] = df['Clasificacion_ABC'].apply(
            lambda x: 'Zona Dorada (cerca de andenes)' if x == 'A' else 'Zona Media' if x == 'B' else 'Zona Fría (fondo)'
        )

        # Guardar clasificación
        df.to_csv(RUTA_CLASIFICACION_ABC, index=False)
        logger.info(f"📄 Clasificación ABC guardada: {len(df)} SKUs.")

        return df

    def detectar_mermas(self, df: pd.DataFrame = None, umbral_abs: int = 5, umbral_pct: float = 10.0) -> pd.DataFrame:
        """
        Detecta SKUs con discrepancias significativas (mermas).
        - umbral_abs: diferencia absoluta mínima para considerar merma.
        - umbral_pct: porcentaje mínimo de desviación.
        """
        if df is None:
            df = self.df_conciliado

        if df is None or df.empty:
            logger.warning("⚠️ No hay datos para detectar mermas.")
            return pd.DataFrame()

        # Filtrar discrepancias significativas
        mermas = df[
            (df['Discrepancia_Abs'] >= umbral_abs) &
            (df['Porcentaje_Desviacion'].abs() >= umbral_pct) &
            (df['Estado'] == 'Normal')
        ].copy()

        # Ordenar por mayor discrepancia
        mermas = mermas.sort_values('Discrepancia_Abs', ascending=False)

        if not mermas.empty:
            # Agregar columna de prioridad
            mermas['Prioridad'] = mermas['Clasificacion_ABC'].apply(
                lambda x: 'Alta' if x == 'A' else ('Media' if x == 'B' else 'Baja')
            )
            mermas.to_csv(RUTA_MERMAS, index=False)
            logger.info(f"📄 Mermas detectadas: {len(mermas)} SKUs.")
        else:
            logger.info("✅ No se detectaron mermas significativas.")

        return mermas

    def generar_reportes(self):
        """
        Genera todos los reportes del módulo de conciliación.
        """
        Path("data/outputs").mkdir(parents=True, exist_ok=True)

        # 1. Discrepancias completas
        if self.df_conciliado is not None and not self.df_conciliado.empty:
            self.df_conciliado.to_csv(RUTA_DISCREPANCIAS, index=False)
            logger.info(f"📄 Discrepancias guardadas: {RUTA_DISCREPANCIAS}")

        # 2. Clasificación ABC
        self.clasificar_abc()

        # 3. Mermas
        self.detectar_mermas()

        # 4. Resumen ejecutivo
        if self.df_conciliado is not None:
            resumen = {
                'Total_SKUs': len(self.df_conciliado),
                'SKUs_Con_Discrepancia': len(self.df_conciliado[self.df_conciliado['Discrepancia'] != 0]),
                'SKUs_Sin_Discrepancia': len(self.df_conciliado[self.df_conciliado['Discrepancia'] == 0]),
                'Inventario_Fantasma': len(self.df_conciliado[self.df_conciliado['Estado'] == 'Fantasma']),
                'Valor_Total_Discrepancia': self.df_conciliado['Discrepancia_Abs'].sum(),
                'SKUs_Clase_A': len(self.df_conciliado[self.df_conciliado['Clasificacion_ABC'] == 'A']),
                'SKUs_Clase_B': len(self.df_conciliado[self.df_conciliado['Clasificacion_ABC'] == 'B']),
                'SKUs_Clase_C': len(self.df_conciliado[self.df_conciliado['Clasificacion_ABC'] == 'C']),
            }
            resumen_df = pd.DataFrame([resumen])
            resumen_df.to_csv("data/outputs/resumen_conciliacion.csv", index=False)
            logger.info("📄 Resumen de conciliación guardado.")

        return


# =====================================================================
# EJECUCIÓN
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("📊 MOTOR DE CONCILIACIÓN DE INVENTARIO")
    print("=" * 60)

    motor = MotorConciliacion()
    motor.cargar_datos()
    motor.conciliar()
    motor.generar_reportes()

    print("\n📁 Archivos generados:")
    print(f"   - {RUTA_DISCREPANCIAS}")
    print(f"   - {RUTA_CLASIFICACION_ABC}")
    print(f"   - {RUTA_MERMAS}")
    print("   - data/outputs/resumen_conciliacion.csv")

    # Mostrar resumen
    if motor.df_conciliado is not None:
        df = motor.df_conciliado
        print("\n📊 Resumen de conciliación:")
        print(f"   Total SKUs: {len(df)}")
        print(f"   SKUs con discrepancia: {len(df[df['Discrepancia'] != 0])}")
        print(f"   Inventario fantasma: {len(df[df['Estado'] == 'Fantasma'])}")
        print(f"   Valor total de discrepancia: ${df['Discrepancia_Abs'].sum():.2f}")
        print(f"   Clase A: {len(df[df['Clasificacion_ABC'] == 'A'])} SKUs")
        print(f"   Clase B: {len(df[df['Clasificacion_ABC'] == 'B'])} SKUs")
        print(f"   Clase C: {len(df[df['Clasificacion_ABC'] == 'C'])} SKUs")
