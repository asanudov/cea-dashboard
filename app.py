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

    if "p1" in v or "presion 1" in v or "presión 1" in v:
        return "P1"

    if "p2" in v or "presion 2" in v or "presión 2" in v:
        return "P2"

    if v == "q" or "caudal" in v or "q (lps)" in v or ("q" in v and "lps" in v):
        return "Q"

    return None

# =====================================================
# ESTILOS (SIN CAMBIOS)
# =====================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Akt:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Akt', sans-serif !important;
    }

    .block-container{
        padding-top: 1rem;
        padding-bottom: 0rem;
    }

    h1, h2, h3 {
        font-family: 'Akt', sans-serif !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        font-family: 'Akt', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        height: 48px !important;
        font-size: 16px !important;
    }

    div[data-testid="stMetric"]{
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
        font-family: 'Akt', sans-serif !important;
    }

    .tabla-cea {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Akt', sans-serif !important;
        font-size: 15px;
        border-radius: 10px;
        overflow: hidden;
    }

    .tabla-cea thead th {
        background-color: #f2f2f2;
        color: #111;
        font-weight: 700;
        padding: 12px;
        text-align: center;
    }

    .tabla-cea tbody td {
        padding: 12px;
        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# HEADER
# =====================================================

col_logo, col_titulo = st.columns([0.7, 4.3])

with col_logo:
    st.image("logo.png", width=110)

with col_titulo:
    st.markdown("<h1>Dashboard para Datos de Gestión de Presiones</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#444;'>Desarrollado por M.I. Alan Sañudo</h3>", unsafe_allow_html=True)

# =====================================================
# UPLOAD
# =====================================================

archivo = st.file_uploader("📂 Subir archivo Excel", type=["xlsx"])

if archivo is None:
    st.info("⬆️ Carga un archivo para comenzar.")

if archivo is not None:

    ejecutar = st.button("▶ Ejecutar cálculo")

    if ejecutar:

        # =====================================================
        # LEER DATOS
        # =====================================================

        df = pd.read_excel(archivo)
        df.columns = df.columns.str.strip()

        df = df.rename(columns={
            "Data Logger": "Variable",
            "Fecha y hora": "FechaHora",
            "Media": "Valor"
        })

        df["FechaHora"] = pd.to_datetime(df["FechaHora"], dayfirst=True)

        df["Valor"] = (
            df["Valor"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        # =====================================================
        # CLASIFICAR
        # =====================================================

        df["Tipo"] = df["Variable"].apply(clasificar_variable)
        df = df[df["Tipo"].notnull()].copy()
        df = df.sort_values("FechaHora")

        p1 = df[df["Tipo"] == "P1"].copy()
        p2 = df[df["Tipo"] == "P2"].copy()
        q = df[df["Tipo"] == "Q"].copy()

        # =====================================================
        # PRESIONES
        # =====================================================

        p1_promedio = p1["Valor"].mean()
        p2_promedio = p2["Valor"].mean()

        # =====================================================
        # Q LIMPIO (sin ceros ni picos)
        # =====================================================

        q_clean = q.copy()
        q_clean["Hora"] = q_clean["FechaHora"].dt.hour

        q_clean = q_clean[q_clean["Valor"] > 0]

        if not q_clean.empty:
            Q1 = q_clean["Valor"].quantile(0.25)
            Q3 = q_clean["Valor"].quantile(0.75)
            IQR = Q3 - Q1
            q_clean = q_clean[q_clean["Valor"] <= (Q3 + 1.5 * IQR)]

        # =====================================================
        # TANDEO
        # =====================================================

        q["Hora"] = q["FechaHora"].dt.hour
        q["is_zero"] = q["Valor"] == 0

        porcentaje_cero = q["is_zero"].mean()
        es_tandeo = porcentaje_cero > 0.4

        # =====================================================
        # Q PROMEDIO FINAL (REGLA CLAVE)
        # =====================================================

        if es_tandeo:
            q_promedio_final = q["Valor"].mean()   # incluye ceros + picos
        else:
            q_promedio_final = q_clean["Valor"].mean()

        # =====================================================
        # VOLUMEN
        # =====================================================

        q["Delta_t_s"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
        q["Volumen_m3"] = (q["Valor"] * q["Delta_t_s"]) / 1000
        volumen_total = q["Volumen_m3"].sum()

        # =====================================================
        # MNF
        # =====================================================

        if es_tandeo:
            nmf = None
            hora_nmf = None
            st.warning("⚠️ Tandeo detectado → MNF desactivado")

        else:

            q_noche = q_clean[(q_clean["Hora"] >= 2) & (q_clean["Hora"] < 4)].copy()

            if not q_noche.empty:

                q_noche = q_noche.sort_values("FechaHora")

                intervalo = q_noche["FechaHora"].diff().dt.total_seconds().median() / 60
                ventana = max(1, int(60 / intervalo))

                q_noche["MNF"] = q_noche["Valor"].rolling(ventana, min_periods=1).mean()

                idx = q_noche["MNF"].idxmin()

                nmf = q_noche.loc[idx, "MNF"]
                hora_nmf = q_noche.loc[idx, "FechaHora"]

            else:
                nmf = None
                hora_nmf = None

        # =====================================================
        # KPIs
        # =====================================================

        st.divider()

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("P. aguas arriba", f"{p1_promedio:.2f} bar")
        col2.metric("P. aguas abajo", f"{p2_promedio:.2f} bar")
        col3.metric("Q promedio", f"{q_promedio_final:.2f} lps")
        col4.metric("Volumen total", f"{volumen_total:.2f} m³")

        if nmf is not None:
            col5.metric("MNF", f"{nmf:.2f} lps")

        # =====================================================
        # TABLA RESUMEN
        # =====================================================

        col_izq, col_der = st.columns([1, 2.3])

        with col_izq:

            st.subheader("📋 Resumen")

            resultado = pd.DataFrame({
                "Indicador": [
                    "P. aguas arriba",
                    "P. aguas abajo",
                    "Q promedio",
                    "Volumen total",
                    "MNF"
                ],
                "Valor": [
                    f"{p1_promedio:.2f}",
                    f"{p2_promedio:.2f}",
                    f"{q_promedio_final:.2f}",
                    f"{volumen_total:.2f}",
                    f"{nmf:.2f}" if nmf is not None else "-"
                ],
                "Unidad": ["bar", "bar", "lps", "m³", "lps"]
            })

            st.markdown(
                resultado.to_html(index=False, classes="tabla-cea"),
                unsafe_allow_html=True
            )

        # =====================================================
        # GRÁFICA (CONSISTENTE CON KPI)
        # =====================================================

        with col_der:

            st.subheader("📉 Serie temporal de caudal")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=q["FechaHora"],
                y=q["Valor"],
                mode="lines",
                name="Caudal en lps",
                line=dict(width=2, color="blue")
            ))

            fig.add_trace(go.Scatter(
                x=[q["FechaHora"].min(), q["FechaHora"].max()],
                y=[q_promedio_final, q_promedio_final],
                mode="lines",
                name="Caudal promedio",
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
                height=420,
                margin=dict(l=10, r=10, t=40, b=10),
                hovermode="x unified",
                xaxis=dict(rangeslider=dict(visible=True)),
                yaxis=dict(range=[q["Valor"].min()*0.9, q["Valor"].max()*1.1]),
                legend=dict(
                    orientation="h",
                    y=1.08,
                    x=0.5,
                    xanchor="center"
                )
            )

            st.plotly_chart(fig, use_container_width=True)

        # =====================================================
        # DESCARGA
        # =====================================================

        st.download_button(
            "📥 Descargar resumen",
            resultado.to_csv(index=False).encode("utf-8"),
            "resumen.csv",
            "text/csv"
        )
