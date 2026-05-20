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
# ESTILOS GLOBALES
# =====================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Akt:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Akt', sans-serif !important;
    }

    .block-container{
        padding-top: 2.5rem !important;
        padding-bottom: 0rem !important;
    }

    h1, h2, h3 {
        font-family: 'Akt', sans-serif !important;
        font-weight: 700 !important;
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
    st.markdown("<div style='padding-top:10px;'></div>", unsafe_allow_html=True)
    st.image("logo.png", width=170)

with col_titulo:

    st.markdown("<h1>Dashboard para Datos de Gestión de Presiones</h1>", unsafe_allow_html=True)

    st.markdown("""
Calcula automáticamente:

- Presión aguas arriba promedio (bar)  
- Presión aguas abajo promedio (bar)  
- Caudal promedio (lps)  
- Volumen total (m³)  
- MNF (Minimum Night Flow)  

**Nota:** el archivo debe ser desde SkyPlatform sin alterar, de preferencia en un periodo mayor a 2 semanas.
""")

# =====================================================
# UPLOAD
# =====================================================

archivo = st.file_uploader("", type=["xlsx"])

if archivo is None:
    st.info("Carga un archivo para comenzar.")

if archivo is not None:

    ejecutar = st.button("▶ Ejecutar cálculo")

    if ejecutar:

        # =====================================================
        # LECTURA
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
        # VARIABLES
        # =====================================================

        df["Tipo"] = df["Variable"].apply(clasificar_variable)
        df = df[df["Tipo"].notnull()].copy()
        df = df.sort_values("FechaHora")

        p1 = df[df["Tipo"] == "P1"].copy()
        p2 = df[df["Tipo"] == "P2"].copy()
        q = df[df["Tipo"] == "Q"].copy()

        # =====================================================
        # KPIs BASE
        # =====================================================

        p1_prom = p1["Valor"].mean()
        p2_prom = p2["Valor"].mean()

        q["Hora"] = q["FechaHora"].dt.hour
        es_tandeo = (q["Valor"] == 0).mean() > 0.4

        if es_tandeo:
            q_prom = q["Valor"].mean()
        else:
            q_prom = q[q["Valor"] > 0]["Valor"].mean()

        # =====================================================
        # VOLUMEN
        # =====================================================

        q["Delta_t"] = q["FechaHora"].diff().dt.total_seconds().fillna(0)
        q["Volumen"] = (q["Valor"] * q["Delta_t"]) / 1000
        volumen = q["Volumen"].sum()

        # =====================================================
        # MNF
        # =====================================================

        q_mnf = q.copy()

        q_mnf["Valor_mnf"] = pd.to_numeric(q_mnf["Valor"], errors="coerce")
        q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].replace(0, pd.NA)
        q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].interpolate(limit=2)
        q_mnf["Valor_mnf"] = q_mnf["Valor_mnf"].ffill().bfill()

        q_mnf["Hora"] = q_mnf["FechaHora"].dt.hour
        q_noche = q_mnf[(q_mnf["Hora"] >= 2) & (q_mnf["Hora"] < 4)]

        nmf = q_noche["Valor_mnf"].min() if not q_noche.empty else None

        # =====================================================
        # RANGO DE FECHAS
        # =====================================================

        fecha_ini = q["FechaHora"].min()
        fecha_fin = q["FechaHora"].max()

        rango_fechas = f"{fecha_ini.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"

        # =====================================================
        # KPIs
        # =====================================================

        st.divider()

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric("P1", f"{p1_prom:.2f} bar")
        c2.metric("P2", f"{p2_prom:.2f} bar")
        c3.metric("Q prom", f"{q_prom:.2f} lps")
        c4.metric("Volumen", f"{volumen:.2f} m³")
        c5.metric("MNF", f"{nmf:.2f}" if nmf else "-")

        # =====================================================
        # KPI PERIODO (AJUSTADO)
        # =====================================================

        c6.markdown(
            f"""
            <div style="
                background-color:#f8f9fa;
                border:1px solid #e6e6e6;
                border-radius:10px;
                padding:10px;
                font-family:'Akt', sans-serif;
                text-align:center;
                height:100%;
                display:flex;
                flex-direction:column;
                justify-content:center;
            ">
                <div style="font-size:12px; font-weight:600;">Periodo</div>
                <div style="font-size:13px; line-height:1.2; margin-top:4px;">
                    {rango_fechas}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # =====================================================
        # TABLA RESUMEN (AKT FIX)
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
                """
                <style>
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
                    font-family: 'Akt', sans-serif !important;
                    font-weight: 700;
                }

                .tabla-cea td {
                    padding: 12px;
                    text-align: center;
                    font-family: 'Akt', sans-serif !important;
                    font-weight: 500;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

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
                legend=dict(
                    orientation="h",
                    y=1.08,
                    x=0.5,
                    xanchor="center"
                )
            )

            st.plotly_chart(fig, use_container_width=True)
