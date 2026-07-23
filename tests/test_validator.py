import pytest
import pandas as pd
from src.validator_preventa import ValidadorPreventa
from src.conciliacion_inventario import MotorConciliacion

# =====================================================================
# COMPONENTE A: VALIDADOR DE PREVENTA
# =====================================================================

def test_validar_skus():
    validador = ValidadorPreventa()
    df = pd.DataFrame({
        'SKU': ['GLS-20001', 'GLS-99999', 'INVALIDO'],
        'ID_Pedido': ['ORD-2026-0001', 'ORD-2026-0002', 'ORD-2026-0003']
    })
    df_validado = validador.validar_skus(df)
    assert df_validado['SKU_Valido'].tolist() == [True, False, False]

def test_validar_formato_pedido():
    validador = ValidadorPreventa()
    df = pd.DataFrame({
        'ID_Pedido': ['ORD-2026-001234', 'ORD-26-1234', 'PEDIDO-001']
    })
    df_validado = validador.validar_formato_pedido(df)
    assert df_validado['Formato_Pedido_Valido'].tolist() == [True, False, False]

def test_ejecutar_validacion():
    validador = ValidadorPreventa()
    df = validador.cargar_ordenes()
    resultados = validador.ejecutar_validacion(df)
    assert 'df_validas' in resultados
    assert 'df_errores' in resultados
    assert 'df_con_validacion' in resultados

# =====================================================================
# COMPONENTE B: CONCILIACIÓN DE INVENTARIO
# =====================================================================

def test_conciliacion():
    motor = MotorConciliacion()
    motor.cargar_datos()
    df = motor.conciliar()
    assert 'Discrepancia' in df.columns
    assert 'Stock_Teorico' in df.columns
    assert 'Stock_Fisico_Real' in df.columns
    assert not df.empty

def test_clasificacion_abc():
    motor = MotorConciliacion()
    motor.cargar_datos()
    motor.conciliar()
    df = motor.clasificar_abc()
    assert 'Clasificacion_ABC' in df.columns
    assert set(df['Clasificacion_ABC'].unique()).issubset({'A', 'B', 'C'})

def test_detectar_mermas():
    motor = MotorConciliacion()
    motor.cargar_datos()
    motor.conciliar()
    mermas = motor.detectar_mermas(umbral_abs=2, umbral_pct=5.0)
    assert 'Prioridad' in mermas.columns if not mermas.empty else True
