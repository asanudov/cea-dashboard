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

/* 1. FUENTE GLOBAL */
html, body, [class*="css"], h1, h2, h3, .stMarkdown, .kpi-box {
    font-family: 'Akt', sans-serif !important;
}

/* 2. ELIMINAR CABECERA Y SUBIR CONTENIDO AL MÁXIMO */
header[data-testid="stHeader"] {
    visibility: hidden;
    display: none !important;
}

[data-testid="stAppViewContainer"] {
    padding-top: 0rem !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important; 
    margin-top: 0rem !important;
}

/* --- JERARQUÍA DE TÍTULOS --- */
h1 {
    font-size: 26px !important; 
    margin-top: 0px !important;
    margin-bottom: 8px !important; 
    padding-top: 0px !important;
    color: #1E293B;
    line-height: 1.2 !important;
}

h3, .section-subtitle {
    font-size: 18px !important; 
    margin-top: 5px !important;
    margin-bottom: 8px !important;
    padding-bottom: 0px !important;
    color: #1E293B;
    font-weight: 600 !important;
}

/* Sustituto compacto para st.divider() */
.compact-divider {
    border-top: 1px solid #e6e6e6;
    margin-top: 12px;
    margin-bottom: 12px;
}

/* 3. ESTILOS DE LA TABLA RESUMEN */
table {
    width: 100%;
    border-collapse: collapse;
}
table thead th {
    background-color: #D1E5F0 !important;
    color: #1E293B !important;
    text-align: left !important;
    padding: 8px !important;
    border: 1px solid #e6e6e6 !important;
    font-size: 14px;
}
table td {
    font-size: 13px;
}

/* 4. SIDEBAR ELEMENTOS */
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] header {
    display: none !important;
}
[data-testid="collapsedControl"] { display: none !important; }

div.stButton > button {
    width: 100%;
    margin-top: 10px;
}

/* 5. KPI BOX - TÍTULO NEGRITA, VALOR NORMAL */
.kpi-box, .kpi-periodo {
    background-color: #f8f9fa;
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    padding: 10px;
    height: 90px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.kpi-title { 
    font-size: 13px; 
    font-weight: 700 !important; 
    margin-bottom: 3px;
}
.kpi-value { 
    font-size: 17px; 
    font-weight: 400 !important; 
}

/* Estilo específico para Periodo (C6) */
.kpi-periodo .kpi-title { font-size: 11px; font-weight: 700 !important; }
.kpi-periodo .kpi-value { font-size: 12px; font-weight: 400 !important; line-height: 1.2; }

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
    - **Presión aguas arriba** (bar)
    - **Presión aguas abajo** (bar)
    - **Caudal promedio** (lps)
    - **Volumen total** ($m^3$)
    - **MNF** (Minimum Night Flow)
    """)
    st.write("---")
    archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])
    ejecutar_calculo = st.button("▶ Ejecutar cálculo")

# =====================================================
# INTERFAZ PRINCIPAL
# =====================================================

st.title("Dashboard de Indicadores en un DMA")

if archivo is None:
    st.info("Carga un archivo desde el panel izquierdo y presiona 'Ejecutar cálculo'.")

if archivo is not None and ejecutar_calculo:
    # 1. Procesamiento y homologación de datos
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Data Logger": "Variable", "Fecha y hora": "FechaHora", "Media": "Valor"})
    df["FechaHora"] = pd.to_datetime(df["FechaHora"], dayfirst=True)
    df["Valor"] = df["Valor"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df["Tipo"] = df["Variable"].apply(clasificar_variable)
    df = df[df["Tipo"].notnull()].copy()
    df = df.sort_values("FechaHora")

    # Separación por variables en dataframes limpios alineados por tiempo
    df_pivot = df.pivot_table(index="FechaHora", columns="Tipo", values="Valor", aggfunc="mean").reset_index()
    df_pivot = df_pivot.sort_values("FechaHora")
    
    # Rellenar columnas faltantes por si acaso
    for col in ["P1", "P2", "Q"]:
        if col not in df_pivot.columns:
            df_pivot[col] = 0.0

    # 2. Identificación de anomalías de red (Problema de suministro en la entrada P1)
    # Si la presión P1 cae por debajo de 0.1 bar, asumimos falla de suministro externo ajeno al DMA
    df_pivot["Falla_Suministro_P1"] = df_pivot["P1"] < 0.1

    p1_data = df_pivot["P1"].dropna()
    p2_data = df_pivot["P2"].dropna()
    q_data = df_pivot[["FechaHora", "Q"]].dropna()

    # 3. Cálculos de Indicadores (KPIs)
    p1_prom = p1_data.mean()
    p2_prom = p2_data.mean()
    
    # Regla de tandeo (Independiente: si el flujo es 0 durante más del 40% de la muestra completa)
    es_tandeo = (q_data["Q"] == 0).mean() > 0.4
    
    if es_tandeo:
        q_prom = q_data["Q"].mean()
    else:
        q_prom = q_data[q_data["Q"] > 0]["Q"].mean()

    # Cálculo del volumen acumulado
    q_data["Delta_t"] = q_data["FechaHora"].diff().dt.total_seconds().fillna(0)
    volumen = (q_data["Q"] * q_data["Delta_t"] / 1000).sum()

    # 4. Cálculo del MNF discriminando "Problema en Suministro (P1)"
    # Creamos una serie limpia para interpolación y análisis nocturno
    q_mnf = df_pivot[["FechaHora", "Q", "Falla_Suministro_P1"]].copy()
    q_mnf["Valor_mnf"] = pd.to_numeric(q_mnf["Q"], errors="coerce")
    
    # Si hay tandeo, los ceros estructurales se mantienen.
    # Pero si NO hay tandeo y el flujo es 0 o P1 falló, lo descartamos de la muestra nocturna del MNF
    if not es_tandeo:
        q_mnf.loc[(q_mnf["Valor_mnf"] == 0) | (q_mnf["Falla_Suministro_P1"] == True), "Valor_mnf"] = pd.NA
    else:
        q_mnf.loc[q_mnf["Falla_Suministro_P1"] == True, "Valor_mnf"] = pd.NA

    # Interpolamos fallas cortas y completamos el dataset nocturno válido
    q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].astype("float64").interpolate(limit=2).ffill().bfill()
    
    # Filtro de horario nocturno de mínimos (2:00 AM - 4:00 AM)
    q_noche = q_mnf[(q_mnf["FechaHora"].dt.hour >= 2) & (q_mnf["FechaHora"].dt.hour < 4)]
    nmf = q_noche["Valor_mnf"].min() if not q_noche.empty else None

    f_min = df_pivot['FechaHora'].min().strftime('%d/%m/%Y')
    f_max = df_pivot['FechaHora'].max().strftime('%d/%m/%Y')

    # =====================================================
    # INDICADORES DEL SECTOR
    # =====================================================
    st.markdown("### Indicadores del Sector")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    def kpi(col, t, v):
        col.markdown(f'<div class="kpi-box"><div class="kpi-title">{t}</div><div class="kpi-value">{v}</div></div>', unsafe_allow_html=True)

    kpi(c1, "P1 (bar)", f"{p1_prom:.2f}")
    kpi(c2, "P2 (bar)", f"{p2_prom:.2f}")
    kpi(c3, "Q prom (lps)", f"{q_prom:.2f}")
    kpi(c4, "Volumen", f"{volumen:.2f} m³")
    kpi(c5, "MNF (lps)", f"{nmf:.2f}" if nmf else "-")
    
    c6.markdown(
        f'<div class="kpi-periodo"><div class="kpi-title">Periodo</div><div class="kpi-value">{f_min}<br>–<br>{f_max}</div></div>', 
        unsafe_allow_html=True
    )

    st.markdown('<div class="compact-divider"></div>', unsafe_allow_html=True)

    # =====================================================
    # CUERPO DEL DASHBOARD (TABLA Y GRÁFICO)
    # =====================================================
    col_tabla, col_grafico = st.columns([1, 2.3])

    with col_tabla:
        st.markdown('<h3 class="section-subtitle">Resumen</h3>', unsafe_allow_html=True)
        resumen = pd.DataFrame({
            "Indicador": ["P1", "P2", "Q prom", "Volumen", "MNF"],
            "Valor": [f"{p1_prom:.2f}", f"{p2_prom:.2f}", f"{q_prom:.2f}", f"{volumen:.2f}", f"{nmf:.2f}" if nmf else "-"],
            "Unidad": ["bar", "bar", "lps", "m³", "lps"]
        })
        st.markdown(resumen.to_html(index=False, escape=False), unsafe_allow_html=True)

    with col_grafico:
        fig = go.Figure()
        
        # Línea de Caudal (Q)
        fig.add_trace(go.Scatter(x=df_pivot["FechaHora"], y=df_pivot["Q"], mode="lines", name="Q", line=dict(width=2, color="blue")))
        
        # Línea de Q promedio
        fig.add_trace(go.Scatter(x=[df_pivot["FechaHora"].min(), df_pivot["FechaHora"].max()], y=[q_prom, q_prom], mode="lines", name="Q prom", line=dict(width=2, color="red", dash="dot")))
        
        # Línea de MNF (Si existe)
        if nmf:
            fig.add_trace(go.Scatter(x=[df_pivot["FechaHora"].min(), df_pivot["FechaHora"].max()], y=[nmf, nmf], mode="lines", name="MNF", line=dict(width=2, color="green", dash="dash")))

        fig.update_layout(
            height=460, 
            margin=dict(t=10, b=10, l=10, r=10),
            hovermode="x unified", 
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
