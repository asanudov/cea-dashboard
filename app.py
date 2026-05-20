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
@import url('https://fonts.googleapis.com/css2?family=Akt:wght@400;500;600;700&display=swap');

/* 1. FUENTE GLOBAL SIN ROMPER ICONOS */
html, body, [class*="css"], h1, h2, h3, .stMarkdown, .kpi-box {
    font-family: 'Akt', sans-serif !important;
}

/* 2. OCULTAR TOTALMENTE EL MENU SUPERIOR Y ELIMINAR EL ESPACIO EN BLANCO */
header[data-testid="stHeader"] {
    visibility: hidden;
    display: none !important;
    height: 0px !important;
}

/* AJUSTE SEGURO DE CONTENEDORES PARA SUBIR EL TITULO SIN OCULTARLO */
[data-testid="stAppViewContainer"] {
    padding-top: 0rem !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 1rem !important; /* Espacio mínimo seguro para que se vea el título */
    padding-bottom: 1rem !important;
    margin-top: 0rem !important;
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

/* 4. SIDEBAR ELEMENTOS */
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

/* 6. RECUADRO REDUCIDO PARA EL PERIODO (COMPACTO) */
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
    font-size: 11px !important;
    font-weight: 600;
}
.kpi-periodo .kpi-value {
    font-size: 12px !important;
    font-weight: 600;
    line-height: 1.3;
}

/* 7. TÍTULO PRINCIPAL */
h1 {
    font-size: 26px !important;
    margin-top: 0px !important;
    margin-bottom: 15px !important;
    color: #1E293B;
    line-height: 1.2 !important;
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
    if "p2" in v or "presion 2" in v: return "P2"
    if "q" in v or "caudal" in v: return "Q"
    return None

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.image("logo.png", width=160)
    st.markdown("""
    Calcula automáticamente desde la hoja de excel de cualquier ConDor de SkyPlatform:
    - **Presión aguas arriba promedio** (bar)
    - **Presión aguas abajo promedio** (bar)
    - **Caudal promedio** (lps)
    - **Volumen total** ($m^3$)
    - **MNF** (Minimum Night Flow)
    """)
    st.write("---")
    
    archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])
    ejecutar_calculo = st.button("▶ Ejecutar cálculo")

# =====================================================
# TÍTULO E INTERFAZ PRINCIPAL
# =====================================================

st.title("Dashboard de Indicadores en un DMA")

if archivo is None:
    st.info("Carga un archivo desde el panel izquierdo y presiona 'Ejecutar cálculo'.")

if archivo is not None and ejecutar_calculo:
    # Procesamiento de datos
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Data Logger": "Variable", "Fecha y hora": "FechaHora", "Media": "Valor"})
    df["FechaHora"] = pd.to_datetime(df["FechaHora"], dayfirst=True)
    df["Valor"] = df["Valor"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df["Tipo"] = df["Variable"].apply(clasificar_variable)
    df = df[df["Tipo"].notnull()].copy()
    df = df.sort_values("FechaHora")

    p1 = df[df["Tipo"] == "P1"]
    p2 = df[df["Tipo"] == "P2"]
    q = df[df["Tipo"] == "Q"]

    # Cálculos de KPIs
    p1_prom = p1["Valor"].mean()
    p2_prom = p2["Valor"].mean()
    q["Hora"] = q["FechaHora"].dt.hour
    es_tandeo = (q["Valor"] == 0).mean() > 0.4
    q_prom = q["Valor"].mean() if es_tandeo else q[q["Valor"] > 0]["Valor"].mean()
    q["Delta_t"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
    volumen = (q["Valor"] * q["Delta_t"] / 1000).sum()

    # MNF Filtrado
    q_mnf = q.copy()
    q_mnf["Valor_mnf"] = pd.to_numeric(q_mnf["Valor"], errors="coerce")
    q_mnf.loc[q_mnf["Valor_mnf"] == 0, "Valor_mnf"] = pd.NA
    q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].astype("float64").interpolate(limit=2).ffill().bfill()
    
    q_noche = q_mnf[(q_mnf["FechaHora"].dt.hour >= 2) & (q_mnf["FechaHora"].dt.hour < 4)]
    nmf = q_noche["Valor_mnf"].min() if not q_noche.empty else None

    fecha_min = q['FechaHora'].min().strftime('%d/%m/%Y')
    fecha_max = q['FechaHora'].max().strftime('%d/%m/%Y')

    # =====================================================
    # INDICADORES (KPIs)
    # =====================================================
    st.markdown("### INDICADORES")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    def kpi(col, t, v):
        col.markdown(f'<div class="kpi-box"><div class="kpi-title">{t}</div><div class="kpi-value">{v}</div></div>', unsafe_allow_html=True)

    kpi(c1, "P1 (bar)", f"{p1_prom:.2f}")
    kpi(c2, "P2 (bar)", f"{p2_prom:.2f}")
    kpi(c3, "Q prom (lps)", f"{q_prom:.2f}")
    kpi(c4, "Volumen", f"{volumen:.2f} m³")
    kpi(c5, "MNF (lps)", f"{nmf:.2f}" if nmf else "-")
    
    # Renderizado exclusivo reducido para Periodo
    c6.markdown(
        f"""
        <div class="kpi-periodo">
            <div class="kpi-title">Periodo</div>
            <div class="kpi-value">{fecha_min}<br>–<br>{fecha_max}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    st.divider()

    # =====================================================
    # CUERPO DEL DASHBOARD
    # =====================================================
    col_tabla, col_grafico = st.columns([1, 2.3])

    with col_tabla:
        st.subheader("Resumen")
        resumen = pd.DataFrame({
            "Indicador": ["P1", "P2", "Q prom", "Volumen", "MNF"],
            "Valor": [f"{p1_prom:.2f}", f"{p2_prom:.2f}", f"{q_prom:.2f}", f"{volumen:.2f}", f"{nmf:.2f}" if nmf else "-"],
            "Unidad": ["bar", "bar", "lps", "m³", "lps"]
        })
        st.markdown(resumen.to_html(index=False, escape=False), unsafe_allow_html=True)

    with col_grafico:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=q["FechaHora"], y=q["Valor"], mode="lines", name="Q", line=dict(width=2, color="blue")))
        fig.add_trace(go.Scatter(x=[q["FechaHora"].min(), q["FechaHora"].max()], y=[q_prom, q_prom], mode="lines", name="Q prom", line=dict(width=2, color="red", dash="dot")))
        if nmf:
            fig.add_trace(go.Scatter(x=[q["FechaHora"].min(), q["FechaHora"].max()], y=[nmf, nmf], mode="lines", name="MNF", line=dict(width=2, color="green", dash="dash")))

        fig.update_layout(
            height=500, 
            hovermode="x unified", 
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
