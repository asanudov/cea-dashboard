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

    /* Estilo para ajustar las métricas e igualar el tamaño */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 8px 12px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
        font-family: 'Akt', sans-serif !important;
        min-height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Ajustar el tamaño de fuente dentro de la métrica de rango de fechas para que no se desborde */
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: calc(14px + 0.3vw) !important;
        line-height: 1.2 !important;
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
# HEADER Y FILA SUPERIOR INTEGRADA (DISTRIBUCIÓN SEGÚN FOTO)
# =====================================================
# Dividimos la pantalla en dos grandes secciones horizontales para colocar los KPI arriba a la derecha
col_izquierda, col_derecha = st.columns([2.5, 3.5])

with col_izquierda:
    # Logo y Títulos
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
        st.image("logo.png", width=110)
    with col_titulo:
        st.markdown("<h2 style='margin:0; font-size:26px;'>Dashboard para Datos de Gestión de Presiones</h2>", unsafe_allow_html=True)
        st.markdown("<h5 style='color:#666; margin:0 0 10px 0;'>Desarrollado por M.I. Alan Sañudo</h5>", unsafe_allow_html=True)
    
    # Viñetas informativas
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
    
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    
    # Selector de archivo y botón integrados abajo de las notas
    col_file, col_btn = st.columns([1.6, 1.1])
    with col_file:
        archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])
    with col_btn:
        st.markdown("<div style='padding-top: 4px;'></div>", unsafe_allow_html=True)
        if archivo is not None:
            ejecutar = st.button("▶ Ejecutar cálculo")
        else:
            st.button("▶ Ejecutar cálculo", disabled=True)

# Contenedor previo para los cálculos
if archivo is None:
    with col_derecha:
        st.info("Carga un archivo Excel para visualizar los indicadores en este espacio.")
else:
    # Ocultamos la lectura dentro de un estado cacheado o directo para procesar antes de dibujar la columna derecha
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Data Logger": "Variable", "Fecha y hora": "FechaHora", "Media": "Valor"})
    df["FechaHora"] = pd.to_datetime(df["FechaHora"], dayfirst=True)
    df["Valor"] = df["Valor"].astype(str).str.replace(",", ".", regex=False).astype(float)

    df["Tipo"] = df["Variable"].apply(clasificar_variable)
    df = df[df["Tipo"].notnull()].copy()
    df = df.sort_values("FechaHora")

    p1 = df[df["Tipo"] == "P1"].copy()
    p2 = df[df["Tipo"] == "P2"].copy()
    q = df[df["Tipo"] == "Q"].copy()

    p1_prom = p1["Valor"].mean() if not p1.empty else 0.0
    p2_prom = p2["Valor"].mean() if not p2.empty else 0.0

    q["Hora"] = q["FechaHora"].dt.hour
    q["is_zero"] = q["Valor"] == 0
    es_tandeo = q["is_zero"].mean() > 0.4 if not q.empty else False

    if es_tandeo:
        q_prom = q["Valor"].mean() if not q.empty else 0.0
    else:
        q_clean = q[q["Valor"] > 0].copy()
        if not q_clean.empty:
            Q1 = q_clean["Valor"].quantile(0.25)
            Q3 = q_clean["Valor"].quantile(0.75)
            IQR = Q3 - Q1
            q_clean = q_clean[q_clean["Valor"] <= (Q3 + 1.5 * IQR)]
        q_prom = q_clean["Valor"].mean() if not q_clean.empty else 0.0

    q["Delta_t"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
    q["Volumen"] = (q["Valor"] * q["Delta_t"]) / 1000
    volumen = q["Volumen"].sum()

    # MNF
    if es_tandeo:
        nmf = None
    else:
        q_mnf = q.copy()
        q_mnf["Valor_mnf"] = pd.to_numeric(q_mnf["Valor"], errors="coerce")
        q_mnf.loc[q_mnf["Valor_mnf"] == 0, "Valor_mnf"] = pd.NA
        q_mnf["is_zero"] = q_mnf["Valor_mnf"].isna()
        q_mnf["block"] = (q_mnf["is_zero"] != q_mnf["is_zero"].shift()).cumsum()
        block_sizes = q_mnf.groupby("block")["is_zero"].transform("size")
        q_mnf = q_mnf[~((q_mnf["is_zero"]) & (block_sizes > 3))].copy()
        q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].interpolate(limit=2).ffill().bfill()
        q_noche = q_mnf[(q_mnf["Hora"] >= 2) & (q_mnf["Hora"] < 4)].copy()

        if not q_noche.empty:
            q_noche = q_noche.sort_values("FechaHora")
            intervalo = q_noche["FechaHora"].diff().dt.total_seconds().median() / 60
            ventana = max(1, int(60 / intervalo))
            q_noche["MNF"] = q_noche["Valor_mnf"].rolling(ventana, min_periods=1).mean()
            nmf = q_noche.loc[q_noche["MNF"].idxmin(), "MNF"]
        else:
            nmf = None

    # Obtener fechas del periodo analizado
    fecha_inicio = df["FechaHora"].min().strftime("%d/%b/%y")
    fecha_fin = df["FechaHora"].max().strftime("%d/%b/%y")

    # =====================================================
    # SECCIÓN DERECHA: SE DIBUJAN LAS MÉTRICAS EN RECUADROS (6 EN TOTAL)
    # =====================================================
    with col_derecha:
        st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
        # Fila 1 de Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("P1 Promedio", f"{p1_prom:.2f} bar")
        c2.metric("P2 Promedio", f"{p2_prom:.2f} bar")
        c3.metric("Caudal Promedio", f"{q_prom:.2f} lps")
        
        st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
        
        # Fila 2 de Métricas
        c4, c5, c6 = st.columns(3)
        c4.metric("Volumen Total", f"{volumen:.2f} m³")
        c5.metric("MNF", f"{nmf:.2f} lps" if nmf is not None else "-")
        c6.metric("Periodo Analizado", f"{fecha_inicio} al {fecha_fin}")

    # Separador sutil antes de los gráficos
    st.markdown("<hr style='margin:20px 0; border:0; border-top:1px solid #eee;'>", unsafe_allow_html=True)

    # =====================================================
    # CUERPO PRINCIPAL: TABLA VS GRÁFICO
    # =====================================================
    if ejecutar:
        col_tabla, col_grafico = st.columns([1, 2.3])

        with col_tabla:
            tabla = pd.DataFrame({
                "Indicador": ["P1", "P2", "Q prom", "Volumen", "MNF"],
                "Valor": [
                    f"{p1_prom:.2f}",
                    f"{p2_prom:.2f}",
                    f"{q_prom:.2f}",
                    f"{volumen:.2f}",
                    f"{nmf:.2f}" if nmf is not None else "-"
                ],
                "Unidad": ["bar", "bar", "lps", "m³", "lps"]
            })

            st.markdown(tabla.to_html(index=False, classes="tabla-cea"), unsafe_allow_html=True)
            
            st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
            st.download_button(
                "Descargar Reporte CSV",
                tabla.to_csv(index=False).encode("utf-8"),
                "resumen.csv",
                "text/csv"
            )
            if es_tandeo:
                st.warning("Nota: Tandeo detectado en la red.")

        with col_grafico:
            fig = go.Figure()

            # Serie Temporal Q
            fig.add_trace(go.Scatter(
                x=q["FechaHora"],
                y=q["Valor"],
                mode="lines",
                name="Q",
                line=dict(width=2, color="blue")
            ))

            # Línea Q Promedio
            fig.add_trace(go.Scatter(
                x=[q["FechaHora"].min(), q["FechaHora"].max()],
                y=[q_prom, q_prom],
                mode="lines",
                name="Q promedio",
                line=dict(width=2, color="red", dash="dot")
            ))

            # Línea MNF si existe
            if nmf is not None:
                fig.add_trace(go.Scatter(
                    x=[q["FechaHora"].min(), q["FechaHora"].max()],
                    y=[nmf, nmf],
                    mode="lines",
                    name="MNF",
                    line=dict(width=2, color="green", dash="dash")
                ))

            # Ajustes de Plotly: RangeSlider Activado + Leyenda compactada
            fig.update_layout(
                height=400, 
                margin=dict(t=10, b=10, l=10, r=10), 
                hovermode="x unified",
                xaxis=dict(
                    rangeslider=dict(visible=True) # <-- REGRESADO EL RANGESLIDER SOLICITADO
                ),
                yaxis=dict(
                    range=[q["Valor"].min() * 0.9, q["Valor"].max() * 1.1]
                ),
                legend=dict(
                    orientation="h",
                    y=1.05, 
                    x=0.5,
                    xanchor="center"
                )
            )

            st.plotly_chart(fig, use_container_width=True)
