import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import unicodedata

# =====================================================
# CONFIGURACIÓN
# =====================================================
st.set_page_config(
    page_title="Dashboard Gestión de Presiones",
    layout="wide"
)

# =====================================================
# NORMALIZACIÓN
# =====================================================
def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

def clasificar_variable(var):
    v = normalizar(var)
    if "p1" in v or "presion 1" in v:
        return "P1"
    if "p2" in v or "presion 2" in v:
        return "P2"
    if "q" in v or "caudal" in v:
        return "Q"
    return None

# =====================================================
# ESTILO Y CORRECCIONES VISUALES (CSS)
# =====================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Akt:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Akt', sans-serif !important;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 0rem;
    }

    h1, h2, h3 {
        font-family: 'Akt', sans-serif !important;
        font-weight: 700 !important;
        margin-bottom: 5px !important;
    }

    /* Ocultar la etiqueta obligatoria del file uploader para hacerlo compacto */
    div[data-testid="stFileUploader"] > label {
        display: none !important;
    }
    
    /* Ajuste de altura interna del uploader */
    div[data-testid="stFileUploaderDropzone"] {
        padding: 6px 10px !important;
    }

    .stButton > button {
        font-family: 'Akt', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        height: 45px !important;
        font-size: 15px !important;
        width: 100%;
    }

    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
        font-family: 'Akt', sans-serif !important;
    }

    .tabla-cea {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Akt', sans-serif !important;
        font-size: 14px;
    }

    .tabla-cea th {
        background-color: #f2f2f2;
        padding: 10px;
        text-align: center;
    }

    .tabla-cea td {
        padding: 10px;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# HEADER (Centrado vertical implícito por columnas)
# =====================================================
col_logo, col_titulo = st.columns([0.8, 5.2])

with col_logo:
    # Se agrega un pequeño espacio superior para asegurar que no se corte arriba
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.image("logo.png", width=120)

with col_titulo:
    st.markdown("<h1 style='margin:0;'>Dashboard para Datos de Gestión de Presiones</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#666; margin:0 0 10px 0;'>Desarrollado por M.I. Alan Sañudo</h4>", unsafe_allow_html=True)
    
    # Lista de viñetas y nota solicitada
    st.markdown(
        """
        **Calcula automáticamente:**
        * **Presión aguas arriba promedio** (bar)
        * **Presión aguas abajo promedio** (bar)
        * **Caudal promedio** (lps)
        * **Volumen total** ($m^3$)
        * **MNF** (Minimum Night Flow)
        
        *<small>**Nota:** El archivo debe ser desde SkyPlatform sin alterar, de preferencia en un periodo de tiempo mayor a 2 semanas.</small>*
        """, 
        unsafe_allow_html=True
    )

st.write("") # Espacio estético

# =====================================================
# FILA DE CONTROL (Uploader estrecho + Botón Ejecutar)
# =====================================================
# Usamos columnas para poner el uploader y el botón juntos en una franja angosta
col_file, col_btn, col_spacer = st.columns(
