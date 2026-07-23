import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
RUTA_CATALOGO = "data/raw/catalogo_skus.csv"
RUTA_ORDENES = "data/raw/ordenes_ventas.csv"
RUTA_ERROR_LOG = "data/outputs/error_log.csv"
RUTA_ORDENES_VALIDAS = "data/outputs/ordenes_validas.csv"

# Patrón regex para validar formato de ID_Pedido (ej. ORD-2026-001234)
PATRON_ORDEN = r'^ORD-\d{4}-\d{6}$'
PATRON_SKU = r'^[A-Z]{2,3}-\d{4,6}$'


class ValidadorPreventa:
    """
    Componente A: Valida órdenes de venta antes de que lleguen al almacén.
    Detecta SKUs inválidos, formatos incorrectos y genera reportes de error.
    """

    def __init__(self, ruta_catalogo: str = RUTA_CATALOGO):
        """
        Inicializa el validador cargando el catálogo maestro de SKUs.
        """
        self.catalogo = self._cargar_catalogo(ruta_catalogo)
        logger.info(f"✅ Catálogo cargado: {len(self.catalogo)} SKUs válidos.")

    def _cargar_catalogo(self, ruta: str) -> pd.DataFrame:
        """Carga el catálogo maestro de SKUs desde archivo CSV."""
        try:
            df = pd.read_csv(ruta)
            # Normalizar: quitar espacios y convertir a string
            df['SKU'] = df['SKU'].astype(str).str.strip()
            logger.info(f"📂 Catálogo cargado: {len(df)} registros.")
            return df
        except FileNotFoundError:
            logger.warning(f"⚠️ Archivo no encontrado: {ruta}. Usando catálogo de ejemplo.")
            return self._generar_catalogo_ejemplo()
        except Exception as e:
            logger.error(f"❌ Error al cargar catálogo: {e}")
            return pd.DataFrame()

    def _generar_catalogo_ejemplo(self) -> pd.DataFrame:
        """Genera un catálogo de ejemplo para pruebas."""
        skus = [
            {"SKU": "GLS-20001", "Descripcion": "Amphibious Alien", "Familia": "Máscaras"},
            {"SKU": "GLS-20002", "Descripcion": "Cinder the White Dragon", "Familia": "Máscaras"},
            {"SKU": "GLS-20003", "Descripcion": "Steampunk Frankenstein", "Familia": "Máscaras"},
            {"SKU": "GLS-20004", "Descripcion": "Ancient Warrior Princess", "Familia": "Máscaras"},
            {"SKU": "GLS-20009", "Descripcion": "Snarling Werewolf", "Familia": "Máscaras"},
            {"SKU": "GLS-20010", "Descripcion": "Grim Jester", "Familia": "Máscaras"},
            {"SKU": "DEC-0101", "Descripcion": "Decorativo 101", "Familia": "Decorativos"},
            {"SKU": "DEC-0102", "Descripcion": "Decorativo 102", "Familia": "Decorativos"},
            {"SKU": "DIS-0101", "Descripcion": "Disfraz 101", "Familia": "Disfraces"},
            {"SKU": "ACC-0101", "Descripcion": "Accesorio 101", "Familia": "Accesorios"},
            {"SKU": "MAQ-0101", "Descripcion": "Maquillaje 101", "Familia": "Maquillajes"},
        ]
        df = pd.DataFrame(skus)
        # Guardar en archivo para futuras ejecuciones
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        df.to_csv(RUTA_CATALOGO, index=False)
        logger.info(f"📂 Catálogo de ejemplo generado: {len(df)} SKUs.")
        return df

    def cargar_ordenes(self, ruta: str = RUTA_ORDENES) -> pd.DataFrame:
        """Carga las órdenes de venta desde archivo CSV."""
        try:
            df = pd.read_csv(ruta)
            # Normalizar columnas
            for col in ['ID_Pedido', 'SKU', 'Agente_Ventas']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            logger.info(f"📂 Órdenes cargadas: {len(df)} registros.")
            return df
        except FileNotFoundError:
            logger.warning(f"⚠️ Archivo no encontrado: {ruta}. Generando órdenes de ejemplo.")
            return self._generar_ordenes_ejemplo()
        except Exception as e:
            logger.error(f"❌ Error al cargar órdenes: {e}")
            return pd.DataFrame()

    def _generar_ordenes_ejemplo(self) -> pd.DataFrame:
        """Genera órdenes de ejemplo para pruebas con errores intencionales."""
        skus_validos = self.catalogo['SKU'].tolist()
        # Mezclar SKUs válidos con algunos inválidos
        skus_mezclados = skus_validos + ['GLS-99999', 'INVALIDO', 'SKU-0000']
        agentes = ['LUPITA', 'WEN', 'FELIPE', 'MARIA', 'JOSE']

        ordenes = []
        for i in range(1, 51):
            orden = {
                'ID_Pedido': f"ORD-2026-{i:06d}" if i % 5 != 0 else f"ORD-26-{i:04d}",
                'SKU': skus_mezclados[i % len(skus_mezclados)],
                'Cantidad': int(abs((i * 7) % 100) + 1),
                'Agente_Ventas': agentes[i % len(agentes)],
                'Fecha_Captura': f"2026-07-{str(i % 28 + 1).zfill(2)}"
            }
            ordenes.append(orden)
        df = pd.DataFrame(ordenes)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        df.to_csv(RUTA_ORDENES, index=False)
        logger.info(f"📂 Órdenes de ejemplo generadas: {len(df)} registros.")
        return df

    def validar_skus(self, df_ordenes: pd.DataFrame) -> pd.DataFrame:
        """
        Valida que los SKUs existan en el catálogo maestro.
        Retorna DataFrame con columna 'SKU_Valido' (True/False).
        """
        skus_validos_set = set(self.catalogo['SKU'].astype(str).str.strip())
        df_ordenes['SKU_Valido'] = df_ordenes['SKU'].isin(skus_validos_set)
        return df_ordenes

    def validar_formato_pedido(self, df_ordenes: pd.DataFrame) -> pd.DataFrame:
        """
        Valida que el ID_Pedido cumpla con el formato oficial (regex).
        """
        df_ordenes['Formato_Pedido_Valido'] = df_ordenes['ID_Pedido'].apply(
            lambda x: bool(re.match(PATRON_ORDEN, str(x).strip()))
        )
        return df_ordenes

    def validar_skus_multiples(self, df_ordenes: pd.DataFrame) -> pd.DataFrame:
        """
        Valida que no haya SKUs con cantidad 0 o negativa.
        """
        df_ordenes['Cantidad_Valida'] = df_ordenes['Cantidad'] > 0
        return df_ordenes

    def ejecutar_validacion(self, df_ordenes: pd.DataFrame) -> dict:
        """
        Ejecuta todas las validaciones y retorna un diccionario con:
        - df_validas: órdenes que pasaron todas las validaciones.
        - df_errores: órdenes que fallaron al menos una validación.
        - df_con_validacion: tabla original con columnas de validación.
        """
        df = df_ordenes.copy()

        # Ejecutar validaciones
        df = self.validar_skus(df)
        df = self.validar_formato_pedido(df)
        df = self.validar_skus_multiples(df)

        # Crear columna de estado general
        df['Validacion_General'] = (
            df['SKU_Valido'] &
            df['Formato_Pedido_Valido'] &
            df['Cantidad_Valida']
        )

        # Separar válidas y errores
        df_validas = df[df['Validacion_General'] == True].copy()
        df_errores = df[df['Validacion_General'] == False].copy()

        # Agregar descripción de errores
        def describir_error(row):
            errores = []
            if not row['SKU_Valido']:
                errores.append(f"SKU inválido: {row['SKU']}")
            if not row['Formato_Pedido_Valido']:
                errores.append(f"Formato ID_Pedido inválido: {row['ID_Pedido']}")
            if not row['Cantidad_Valida']:
                errores.append(f"Cantidad inválida: {row['Cantidad']}")
            return " | ".join(errores) if errores else "OK"

        df_errores['Descripcion_Error'] = df_errores.apply(describir_error, axis=1)
        df_validas['Descripcion_Error'] = 'OK'

        return {
            'df_validas': df_validas,
            'df_errores': df_errores,
            'df_con_validacion': df
        }

    def generar_reportes(self, resultados: dict):
        """
        Guarda los reportes en archivos CSV.
        - error_log.csv: órdenes rechazadas con motivo.
        - ordenes_validas.csv: órdenes que pasaron la validación.
        - resumen_validacion.csv: resumen estadístico.
        """
        Path("data/outputs").mkdir(parents=True, exist_ok=True)

        # Guardar errores
        df_errores = resultados['df_errores']
        if not df_errores.empty:
            df_errores.to_csv(RUTA_ERROR_LOG, index=False)
            logger.info(f"📄 Error log guardado: {len(df_errores)} órdenes rechazadas.")
        else:
            logger.info("✅ Todas las órdenes pasaron la validación. Sin errores.")

        # Guardar válidas
        df_validas = resultados['df_validas']
        if not df_validas.empty:
            df_validas.to_csv(RUTA_ORDENES_VALIDAS, index=False)
            logger.info(f"📄 Órdenes válidas guardadas: {len(df_validas)} registros.")

        # Generar resumen
        resumen = {
            'Total_Ordenes': len(resultados['df_con_validacion']),
            'Ordenes_Validas': len(df_validas),
            'Ordenes_Rechazadas': len(df_errores),
            'Tasa_Aprobacion': f"{len(df_validas) / len(resultados['df_con_validacion']) * 100:.1f}%",
            'Agentes_Con_Errores': df_errores['Agente_Ventas'].unique().tolist() if not df_errores.empty else []
        }
        resumen_df = pd.DataFrame([resumen])
        resumen_df.to_csv("data/outputs/resumen_validacion.csv", index=False)
        logger.info("📄 Resumen de validación guardado.")

        return resumen


# =====================================================================
# EJECUCIÓN
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ MÓDULO DE VALIDACIÓN DE PREVENTA")
    print("=" * 60)

    validador = ValidadorPreventa()
    ordenes = validador.cargar_ordenes()
    print(f"📊 Órdenes cargadas: {len(ordenes)}")

    resultados = validador.ejecutar_validacion(ordenes)
    resumen = validador.generar_reportes(resultados)

    print("\n📊 Resumen de validación:")
    print(f"   Total de órdenes: {resumen['Total_Ordenes']}")
    print(f"   ✅ Válidas: {resumen['Ordenes_Validas']}")
    print(f"   ❌ Rechazadas: {resumen['Ordenes_Rechazadas']}")
    print(f"   📈 Tasa de aprobación: {resumen['Tasa_Aprobacion']}")

    if resumen['Agentes_Con_Errores']:
        print(f"   👤 Agentes con errores: {', '.join(resumen['Agentes_Con_Errores'])}")
    else:
        print("   🎉 Todos los agentes sin errores.")

    print("\n📁 Archivos generados:")
    print(f"   - {RUTA_ERROR_LOG}")
    print(f"   - {RUTA_ORDENES_VALIDAS}")
    print("   - data/outputs/resumen_validacion.csv")
