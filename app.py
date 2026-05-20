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
# ESTILOS
# =====================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Akt:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], div, span, p, h1, h2, h3 {
        font-family: 'Akt', sans-serif !important;
    }

    .block-container{
        padding-top: 2.5rem !important;
        padding-bottom: 0rem !important;
    }

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

    .kpi-title {
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 18px;
        font-weight: 600;
    }

    /* 🔥 OCULTAR TEXTO EXTRA DEL UPLOADER */
    section[data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }

    </style>
    """,
    unsafe_allow_html=True
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
# HEADER
# =====================================================

col_logo, col_titulo = st.columns([0.8, 4.2])

with col_logo:
    st.image("logo.png", width=170)

with col_titulo:
    st.markdown("<h1>Dashboard para Datos de Gestión de Presiones</h1>", unsafe_allow_html=True)

    st.markdown("""
### Calcula automáticamente:

1. Presión aguas arriba promedio (bar)  
2. Presión aguas abajo promedio (bar)  
3. Caudal promedio (lps)  
4. Volumen total (m³)  
5. MNF (Minimum Night Flow)  

**Desarrollado por M.I. Alan Sañudo**
""")

# =====================================================
# UPLOAD (CAMBIADO CORRECTAMENTE)
# =====================================================

archivo = st.file_uploader("Cargar archivo", type=["xlsx"])

if archivo is None:
    st.info("Carga un archivo para comenzar.")

if archivo is not None and st.button("▶ Cargar archivo"):

    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "Data Logger": "Variable",
        "Fecha y hora": "FechaHora",
        "Media": "Valor"
    })

    df["FechaHora"] = pd.to_datetime(df["FechaHora"], dayfirst=True)

    df["Valor"] = (
        df["Valor"].astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["Tipo"] = df["Variable"].apply(clasificar_variable)
    df = df[df["Tipo"].notnull()].copy()
    df = df.sort_values("FechaHora")

    p1 = df[df["Tipo"] == "P1"]
    p2 = df[df["Tipo"] == "P2"]
    q = df[df["Tipo"] == "Q"]

    # =====================================================
    # KPIs
    # =====================================================

    p1_prom = p1["Valor"].mean()
    p2_prom = p2["Valor"].mean()

    q["Hora"] = q["FechaHora"].dt.hour
    es_tandeo = (q["Valor"] == 0).mean() > 0.4

    if es_tandeo:
        q_prom = q["Valor"].mean()
    else:
        q_prom = q[q["Valor"] > 0]["Valor"].mean()

    q["Delta_t"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
    volumen = (q["Valor"] * q["Delta_t"] / 1000).sum()

    # =====================================================
    # MNF
    # =====================================================

    q_mnf = q.copy()
    q_mnf["Valor_mnf"] = pd.to_numeric(q_mnf["Valor"], errors="coerce")
    q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].replace(0, pd.NA)
    q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].interpolate(limit=2).ffill().bfill()

    q_noche = q_mnf[(q_mnf["FechaHora"].dt.hour >= 2) & (q_mnf["FechaHora"].dt.hour < 4)]
    nmf = q_noche["Valor_mnf"].min() if not q_noche.empty else None

    # =====================================================
    # RANGO
    # =====================================================

    rango = f"{q['FechaHora'].min().strftime('%d/%m/%Y')} - {q['FechaHora'].max().strftime('%d/%m/%Y')}"

    # =====================================================
    # KPIs UI
    # =====================================================

    st.divider()

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def kpi(col, t, v):
        col.markdown(
            f"""
            <div class="kpi-box">
                <div class="kpi-title">{t}</div>
                <div class="kpi-value">{v}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    kpi(c1, "P1", f"{p1_prom:.2f} bar")
    kpi(c2, "P2", f"{p2_prom:.2f} bar")
    kpi(c3, "Q prom (lps)", f"{q_prom:.2f}")
    kpi(c4, "Volumen", f"{volumen:.2f} m³")
    kpi(c5, "MNF (lps)", f"{nmf:.2f}" if nmf else "-")
    kpi(c6, "Periodo", rango)

    # =====================================================
    # TABLA (SIN CAMBIOS)
    # =====================================================

    col1, col2 = st.columns([1, 2.3])

    with col1:
        st.subheader("📋 Resumen")

        resumen = pd.DataFrame({
            "Indicador": ["P1", "P2", "Q prom", "Volumen", "MNF"],
            "Valor": [
                f"{p1_prom:.2f}",
                f"{p2_prom:.2f}",
                f"{q_prom:.2f}",
                f"{volumen:.2f}",
                f"{nmf:.2f}" if nmf else "-"
            ],
            "Unidad": ["bar", "bar", "lps", "m³", "lps"]
        })

        st.markdown(
            resumen.to_html(index=False, classes="tabla-cea"),
            unsafe_allow_html=True
        )

    # =====================================================
    # GRÁFICO
    # =====================================================

    with col2:

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=q["FechaHora"],
            y=q["Valor"],
            mode="lines",
            name="Q",
            line=dict(width=2, color="blue")
        ))

        fig.add_trace(go.Scatter(
            x=[q["FechaHora"].min(), q["FechaHora"].max()],
            y=[q_prom, q_prom],
            mode="lines",
            name="Q prom",
            line=dict(width=2, color="red", dash="dot")
        ))

        if nmf is not None:
            fig.add_trace(go.Scatter(
                x=[q["FechaHora"].min(), q["FechaHora"].max()],
                y=[nmf, nmf],
                mode="lines",
                name="MNF",
                line=dict(width=2, color="green", dash="dash")
            ))

        fig.update_layout(
            height=550,
            hovermode="x unified",
            xaxis=dict(rangeslider=dict(visible=True)),
            legend=dict(
                orientation="h",
                y=1.08,
                x=0.5,
                xanchor="center"
            )
        )

        st.plotly_chart(fig, use_container_width=True)
