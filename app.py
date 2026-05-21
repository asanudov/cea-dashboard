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

/* Alertas de Suministro */
.alerta-suministro {
    background-color: #FFEAEA;
    color: #CC0000;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    border: 1px solid #FFAAAA;
}

.alerta-tandeo {
    background-color: #EAF2FF;
    color: #0044CC;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    border: 1px solid #AABFFF;
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
    # 1. Procesamiento e independización de Series
    df_raw = pd.read_excel(archivo)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw = df_raw.rename(columns={"Data Logger": "Variable", "Fecha y hora": "FechaHora", "Media": "Valor"})
    df_raw["FechaHora"] = pd.to_datetime(df_raw["FechaHora"], dayfirst=True)
    df_raw["Valor"] = df_raw["Valor"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df_raw["Tipo"] = df_raw["Variable"].apply(clasificar_variable)
    
    # Extraer dataframes independientes por variable
    p1 = df_raw[df_raw["Tipo"] == "P1"].sort_values("FechaHora").copy()
    p2 = df_raw[df_raw["Tipo"] == "P2"].sort_values("FechaHora").copy()
    q = df_raw[df_raw["Tipo"] == "Q"].sort_values("FechaHora").copy()

    # 2. Análisis y Diagnóstico Dinámico del Tipo de Suministro
    es_tandeo = False
    hay_interrupcion = False
    fechas_falla_p1 = set()

    if not q.empty:
        # Tandeo detectado si pasa cerrado/mínimo (< 0.15 lps) más del 35% del tiempo total
        es_tandeo = (q["Valor"] <= 0.15).mean() > 0.35

    if not es_tandeo and not p1.empty:
        p1["SoloFecha"] = p1["FechaHora"].dt.strftime('%Y-%m-%d')
        p1["EsBaja"] = p1["Valor"] < 0.15
        resumen_diario_p1 = p1.groupby("SoloFecha")["EsBaja"].mean()
        fechas_falla_p1 = set(resumen_diario_p1[resumen_diario_p1 > 0.15].index)
        hay_interrupcion = len(fechas_falla_p1) > 0

    # 3. Cálculos Generales de Indicadores (KPIs)
    p1_prom = p1["Valor"].mean() if not p1.empty else 0.0
    p2_prom = p2["Valor"].mean() if not p2.empty else 0.0
    
    if es_tandeo:
        q_prom = q["Valor"].mean() if not q.empty else 0.0
    else:
        q_valido_prom = q.copy()
        if hay_interrupcion:
            q_valido_prom = q_valido_prom[~q_valido_prom["FechaHora"].dt.strftime('%Y-%m-%d').isin(fechas_falla_p1)]
        q_prom = q_valido_prom[q_valido_prom["Valor"] > 0.1]["Valor"].mean() if not q_valido_prom.empty else 0.0

    # Cálculo preciso del Volumen Integrado
    if not q.empty:
        q["Delta_t"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
        volumen = (q["Valor"] * q["Delta_t"] / 1000).sum()
        f_min = q['FechaHora'].min().strftime('%d/%m/%Y')
        f_max = q['FechaHora'].max().strftime('%d/%m/%Y')
    else:
        volumen = 0.0
        f_min = f_max = "-/-/-"

    # 4. Cálculo de MNF e Indicadores de Estrés por Tandeo (Pico de Apertura)
    nmf = None
    q_pico_apertura = None
    
    if not q.empty:
        q_mnf = q.copy()
        
        if es_tandeo:
            # A. Extraemos el MNF real (Demanda base en periodos estables con red llena)
            q_activos = q_mnf[q_mnf["Valor"] > 0.5]
            if not q_activos.empty:
                nmf = q_activos["Valor"].quantile(0.05)
                
            # B. CRÍTICO: Identificar el Pico de Apertura de la Válvula
            # Buscamos el valor máximo absoluto del caudal que represente ese transitorio de llenado brusco
            q_pico_apertura = q_mnf["Valor"].max()
            
        else:
            q_mnf["SoloFecha"] = q_mnf["FechaHora"].dt.strftime('%Y-%m-%d')
            if hay_interrupcion:
                q_mnf = q_mnf[~q_mnf["SoloFecha"].isin(fechas_falla_p1)]
                
            q_noche = q_mnf[(q_mnf["FechaHora"].dt.hour >= 2) & (q_mnf["FechaHora"].dt.hour < 4)].copy()
            q_noche = q_noche[q_noche["Valor"] > 0.05]
            if not q_noche.empty:
                nmf = q_noche["Valor"].min()

    # =====================================================
    # INDICADORES DEL SECTOR
    # =====================================================
    st.markdown("### Indicadores del Sector")
    
    if es_tandeo:
        st.markdown('<div class="alerta-tandeo">🔄 Suministro Intermitente (Tandeo Detectado)</div>', unsafe_allow_html=True)
    elif hay_interrupcion:
        st.markdown('<div class="alerta-suministro">⚠️ Detección de interrupción en el suministro</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    def kpi(col, t, v):
        col.markdown(f'<div class="kpi-box"><div class="kpi-title">{t}</div><div class="kpi-value">{v}</div></div>', unsafe_allow_html=True)

    kpi(c1, "P1 (bar)", f"{p1_prom:.2f}")
    kpi(c2, "P2 (bar)", f"{p2_prom:.2f}")
    kpi(c3, "Q prom (lps)", f"{q_prom:.2f}")
    kpi(c4, "Volumen", f"{volumen:.2f} m³")
    
    # Cambiamos dinámicamente el título del KPI si hay tandeo para alertar sobre el pico
    if es_tandeo and q_pico_apertura is not None:
        kpi(c5, "Q Pico Apertura (lps)", f"{q_pico_apertura:.2f}")
    else:
        kpi(c5, "MNF (lps)", f"{nmf:.2f}" if nmf is not None else "-")
    
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
        
        # En la tabla de resumen incluimos AMBOS valores si es tandeo para un análisis completo
        indicadores_lista = ["P1", "P2", "Q prom", "Volumen", "MNF"]
        valores_lista = [f"{p1_prom:.2f}", f"{p2_prom:.2f}", f"{q_prom:.2f}", f"{volumen:.2f}", f"{nmf:.2f}" if nmf is not None else "-"]
        unidades_lista = ["bar", "bar", "lps", "m³", "lps"]
        
        if es_tandeo and q_pico_apertura is not None:
            indicadores_lista.append("Q Pico Apertura")
            valores_lista.append(f"{q_pico_apertura:.2f}")
            unidades_lista.append("lps")

        resumen = pd.DataFrame({
            "Indicador": indicadores_lista,
            "Valor": valores_lista,
            "Unidad": unidades_lista
        })
        st.markdown(resumen.to_html(index=False, escape=False), unsafe_allow_html=True)

    with col_grafico:
        fig = go.Figure()
        
        if not q.empty:
            fig.add_trace(go.Scatter(x=q["FechaHora"], y=q["Valor"], mode="lines", name="Q", line=dict(width=2, color="blue")))
            fig.add_trace(go.Scatter(x=[q["FechaHora"].min(), q["FechaHora"].max()], y=[q_prom, q_prom], mode="lines", name="Q prom", line=dict(width=1.5, color="red", dash="dot")))
            
            if nmf is not None:
                fig.add_trace(go.Scatter(x=[q["FechaHora"].min(), q["FechaHora"].max()], y=[nmf, nmf], mode="lines", name="MNF Base", line=dict(width=2, color="green", dash="dash")))
            
            # Dibujar línea indicadora del pico crítico de apertura si hay tandeo
            if es_tandeo and q_pico_apertura is not None:
                fig.add_trace(go.Scatter(x=[q["FechaHora"].min(), q["FechaHora"].max()], y=[q_pico_apertura, q_pico_apertura], mode="lines", name="Pico de Apertura", line=dict(width=1.5, color="purple", dash="longdashdot")))

        fig.update_layout(
            height=460, 
            margin=dict(t=10, b=10, l=10, r=10),
            hovermode="x unified", 
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig, use_container_width=True)
