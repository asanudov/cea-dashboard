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
# NORMALIZACIÓN DE VARIABLES
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

    # PRESIÓN 1
    if "p1" in v or "presion 1" in v:
        return "P1"

    # PRESIÓN 2
    if "p2" in v or "presion 2" in v:
        return "P2"

    # CAUDAL
    if "q" in v or "caudal" in v:
        return "Q"

    return None

# =====================================================
# ESTILO (INTACTO)
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
    }

    .tabla-cea th {
        background-color: #f2f2f2;
        padding: 12px;
        text-align: center;
    }

    .tabla-cea td {
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
    st.info("Carga un archivo para comenzar.")

if archivo is not None:

    ejecutar = st.button("▶ Ejecutar cálculo")

    if ejecutar:

        # =====================================================
        # LEER
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

        p1_prom = p1["Valor"].mean()
        p2_prom = p2["Valor"].mean()

        # =====================================================
        # TANDEO
        # =====================================================

        q["Hora"] = q["FechaHora"].dt.hour
        q["is_zero"] = q["Valor"] == 0

        es_tandeo = q["is_zero"].mean() > 0.4

        # =====================================================
        # Q PROMEDIO
        # =====================================================

        if es_tandeo:
            q_prom = q["Valor"].mean()   # incluye ceros + picos
        else:
            q_clean = q.copy()
            q_clean = q_clean[q_clean["Valor"] > 0]

            # outliers
            if not q_clean.empty:
                Q1 = q_clean["Valor"].quantile(0.25)
                Q3 = q_clean["Valor"].quantile(0.75)
                IQR = Q3 - Q1
                q_clean = q_clean[q_clean["Valor"] <= (Q3 + 1.5 * IQR)]

            q_prom = q_clean["Valor"].mean()

        # =====================================================
        # VOLUMEN
        # =====================================================

        q["Delta_t"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
        q["Volumen"] = (q["Valor"] * q["Delta_t"]) / 1000
        volumen = q["Volumen"].sum()

        # =====================================================
        # MNF (CON CEROS AISLADOS CORREGIDOS)
        # =====================================================

        if es_tandeo:
            nmf = None
            hora_nmf = None
            st.warning("Tandeo detectado → MNF desactivado")

        else:

            q_mnf = q.copy()
            q_mnf["Valor_mnf"] = q_mnf["Valor"].replace(0, pd.NA)
            q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].interpolate(limit=2)
            q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].ffill().bfill()

            q_mnf["Hora"] = q_mnf["FechaHora"].dt.hour

            q_noche = q_mnf[(q_mnf["Hora"] >= 2) & (q_mnf["Hora"] < 4)].copy()

            if not q_noche.empty:

                q_noche = q_noche.sort_values("FechaHora")

                intervalo = q_noche["FechaHora"].diff().dt.total_seconds().median() / 60
                ventana = max(1, int(60 / intervalo))

                q_noche["MNF"] = q_noche["Valor_mnf"].rolling(
                    ventana,
                    min_periods=1
                ).mean()

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

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("P1", f"{p1_prom:.2f} bar")
        c2.metric("P2", f"{p2_prom:.2f} bar")
        c3.metric("Q prom", f"{q_prom:.2f} lps")
        c4.metric("Volumen", f"{volumen:.2f} m³")

        if nmf is not None:
            c5.metric("MNF", f"{nmf:.2f} lps")

        # =====================================================
        # TABLA
        # =====================================================

        col1, col2 = st.columns([1, 2.3])

        with col1:

            st.subheader("Resumen")

            tabla = pd.DataFrame({
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

            st.markdown(tabla.to_html(index=False, classes="tabla-cea"),
                        unsafe_allow_html=True)

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
                name="Q promedio",
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
                hovermode="x unified",
                xaxis=dict(rangeslider=dict(visible=True)),
                yaxis=dict(range=[q["Valor"].min()*0.9, q["Valor"].max()*1.1]),
                legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center")
            )

            st.plotly_chart(fig, use_container_width=True)

        # =====================================================
        # DESCARGA
        # =====================================================

        st.download_button(
            "Descargar",
            tabla.to_csv(index=False).encode("utf-8"),
            "resumen.csv",
            "text/csv"
        )
