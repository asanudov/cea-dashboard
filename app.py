import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import unicodedata

# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Dashboard de Indicadores en un DMA",
    layout="wide"
)

# =====================================================
# ESTILOS CSS PERSONALIZADOS
# =====================================================

st.markdown(
"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Akt:wght=400;500;600;700&display=swap');

/* 1. FUENTE GLOBAL SIN ROMPER ICONOS */
html, body, [class*="css"], h1, h2, h3, .stMarkdown, .kpi-box {
    font-family: 'Akt', sans-serif !important;
}

/* 2. ELIMINAR TOTALMENTE EL MENÚ Y EL ESPACIO MAGENTA SUPERIOR */
header[data-testid="stHeader"] {
    visibility: hidden;
    display: none !important;
    height: 0px !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 0rem !important;
    margin-top: -3.5rem !important; /* Desplaza el contenido hacia arriba */
}

/* 3. ESTILO DE LA TABLA RESUMEN */
table {
    width: 100%;
    border-collapse: collapse;
}
table thead th {
    background-color: #D1E5F0 !important; /* Azul claro */
    color: #1E293B !important;
    text-align: left !important;
    padding: 10px !important;
    border: 1px solid #e6e6e6 !important;
}
table td {
    padding: 8px !important;
    border: 1px solid #e6e6e6 !important;
}

/* 4. SIDEBAR ELEMENTOS OMINOSOS */
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] header {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
section[data-testid="stFileUploaderDropzoneLabel"] {
    display: none !important;
}
section[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

/* Botón del sidebar a lo ancho */
div.stButton > button {
    width: 100%;
    margin-top: 10px;
}

/* 5. KPI BOX GENÉRICOS */
.kpi-box {
    background-color: #f8f9fa;
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    padding: 10px;
    height: 95px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.kpi-title { font-size: 14px; font-weight: 600; }
.kpi-value { font-size: 18px; font-weight: 600; }

/* 6. CORRECCIÓN EXCLUSIVA PARA EL MARCO EN AZUL CIELO (PERIODO) */
.kpi-periodo {
    background-color: #f8f9fa;
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    padding: 8px;
    height: 95px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.kpi-periodo .kpi-title {
    font-size: 11px !important; /* Título más pequeño */
    font-weight: 600;
}
.kpi-periodo .kpi-value {
    font-size: 12px !important; /* Fechas compactas para que quepan en el recuadro */
    font-weight: 600;
    line-height: 1.3;
}

/* 7. TÍTULO PRINCIPAL */
h1 {
    font-size: 26px !important;
    margin-top: 0px !important;
    margin-bottom: 10px !important;
    color: #1E293B;
}
</style>
""",
unsafe_allow_html=True
)

# =====================================================
# FUNCIONES DE APOYO
# =====================================================

def normalizar(texto):
    if pd.isna(texto): return ""
    texto = str(texto).strip().lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

def clasificar_variable(var):
    v = normalizar(var)
    if "p1" in v or "presion 1" in v: return "P1"
    if "p2
