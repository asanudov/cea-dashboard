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

    # =========================
    # PRESIÓN 1
    # =========================
    if v in ["p1", "presion 1", "presion1", "p1 (bar)", "presion 1 (bar)"]:
        return "P1"

    # =========================
    # PRESIÓN 2
    # =========================
    if v in ["p2", "presion 2", "presion2", "p2 (bar)", "presion 2 (bar)"]:
        return "P2"

    # =========================
    # CAUDAL
    # =========================
    if v in ["q", "caudal", "q (lps)", "caudal (lps)"]:
        return "Q"

    return None
# =====================================================
# ESTILOS
# =====================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Akt:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Akt', sans-serif !important;
    }

    .block-container { padding-top: 1rem; padding-bottom: 0rem; }

    h1, h2, h3 { font-weight: 700 !important; }

    .tabla-cea {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Akt', sans-serif;
    }

    .tabla-cea thead th {
        background: #f2f2f2;
        padding: 12px;
        font-weight: 700;
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
    st.markdown("<h1>Dashboard Gestión de Presiones</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#444;'>M.I. Alan Sañudo</h3>", unsafe_allow_html=True)

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
        # CLASIFICAR VARIABLES
        # =====================================================

        df["Tipo"] = df["Variable"].apply(clasificar_variable)
        df = df[df["Tipo"].notnull()].copy()
        df = df.sort_values("FechaHora")

        # =====================================================
        # SEPARAR VARIABLES
        # =====================================================

        p1 = df[df["Tipo"] == "P1"].copy()
        p2 = df[df["Tipo"] == "P2"].copy()
        q = df[df["Tipo"] == "Q"].copy()

        # =====================================================
        # PROMEDIOS BÁSICOS
        # =====================================================

        p1_promedio = p1["Valor"].mean()
        p2_promedio = p2["Valor"].mean()

        # =====================================================
        # DETECCIÓN DE TANDEO
        # =====================================================

        q = q.sort_values("FechaHora")
        q["Fecha"] = q["FechaHora"].dt.date
        q["Hora"] = q["FechaHora"].dt.hour

        porcentaje_cero = (q["Valor"] == 0).mean()

        q["is_zero"] = q["Valor"] == 0
        q["block"] = (q["is_zero"] != q["is_zero"].shift()).cumsum()

        bloques = q[q["is_zero"]].groupby("block")["FechaHora"].agg(
            lambda x: (x.max() - x.min()).total_seconds() / 3600
        )

        max_bloque_cero = bloques.max() if not bloques.empty else 0

        es_tandeo = (porcentaje_cero > 0.4) or (max_bloque_cero >= 6)

        # =====================================================
        # Q PROMEDIO (AJUSTADO)
        # =====================================================

        if es_tandeo:
            q_promedio = q[q["Valor"] > 0]["Valor"].mean()
        else:
            q_promedio = q["Valor"].mean()

        # =====================================================
        # VOLUMEN
        # =====================================================

        q["Delta_t_s"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
        q["Volumen_m3"] = (q["Valor"] * q["Delta_t_s"]) / 1000
        volumen_total = q["Volumen_m3"].sum()

        # =====================================================
        # MNF (SOLO SI NO HAY TANDEO)
        # =====================================================

        if es_tandeo:

            nmf = None
            hora_nmf = None

            st.warning("⚠️ Sistema en tandeo detectado: MNF desactivado.")

        else:

            q_noche = q[(q["Hora"] >= 2) & (q["Hora"] < 4)].copy()

            if not q_noche.empty:

                q_noche = q_noche.sort_values("FechaHora")

                intervalo_min = q_noche["FechaHora"].diff().dt.total_seconds().median() / 60
                muestras_60min = max(1, int(60 / intervalo_min))

                q_noche["Rolling_MNF"] = (
                    q_noche["Valor"]
                    .rolling(window=muestras_60min, min_periods=1)
                    .mean()
                )

                idx_nmf = q_noche["Rolling_MNF"].idxmin()

                nmf = q_noche.loc[idx_nmf, "Rolling_MNF"]
                hora_nmf = q_noche.loc[idx_nmf, "FechaHora"]

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
        col3.metric("Q promedio", f"{q_promedio:.2f} lps")
        col4.metric("Volumen total", f"{volumen_total:.2f} m³")

        if nmf is not None:
            col5.metric("MNF", f"{nmf:.2f} lps")

        # =====================================================
        # TABLA
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
                    f"{q_promedio:.2f}",
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
        # GRÁFICA
        # =====================================================

        with col_der:

            st.subheader("📉 Serie temporal de caudal")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=q["FechaHora"],
                y=q["Valor"],
                mode="lines",
                name="Caudal"
            ))

            if nmf is not None:
                fig.add_trace(go.Scatter(
                    x=[q["FechaHora"].min(), q["FechaHora"].max()],
                    y=[nmf, nmf],
                    mode="lines",
                    name="MNF"
                ))

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
