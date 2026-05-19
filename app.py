import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Dashboard Gestión de Presiones",
    layout="wide"
)

# =====================================================
# ESTILO COMPACTO
# =====================================================

st.markdown("""
<style>

.block-container{
    padding-top: 1rem;
    padding-bottom: 0rem;
}

div[data-testid="stMetric"]{
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid #e6e6e6;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER CON LOGO
# =====================================================

col_logo, col_titulo = st.columns([1,4])

col_logo, col_titulo = st.columns([0.7,4.3])

with col_logo:

    st.markdown("<div style='padding-top:25px;'></div>", unsafe_allow_html=True)

    st.image(
        "logo.png",
        width=110
    )

with col_titulo:

    st.markdown(
        """
        <h1 style='margin-bottom:0px;'>
        Dashboard para Datos de Gestión de Presiones
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <h3 style='margin-top:0px; color:#444444;'>
        Desarrollado por M.I. Alan Sañudo
        </h3>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# CARGAR ARCHIVO
# =====================================================

archivo = st.file_uploader(
    "📂 Subir archivo Excel",
    type=["xlsx"]
)

# =====================================================
# DESCRIPCIÓN SOLO SI NO HAY ARCHIVO
# =====================================================

if archivo is None:

    st.markdown("""
    ### Calcula automáticamente:
    
    - Presión aguas arriba promedio (bar)
    - Presión aguas abajo promedio (bar)
    - Caudal promedio (lps)
    - Volumen total (m³)
    - MNF (Minimum Night Flow)
    """)

    st.info("⬆️ Carga un archivo para comenzar.")

# =====================================================
# PROCESAMIENTO
# =====================================================

if archivo is not None:

    ejecutar = st.button("▶ Ejecutar cálculo")

    if ejecutar:

        # =====================================================
        # LEER EXCEL
        # =====================================================

        df = pd.read_excel(archivo)

        # =====================================================
        # LIMPIAR COLUMNAS
        # =====================================================

        df.columns = df.columns.str.strip()

        # =====================================================
        # RENOMBRAR
        # =====================================================

        df = df.rename(columns={
            "Data Logger": "Variable",
            "Fecha y hora": "FechaHora",
            "Media": "Valor"
        })

        # =====================================================
        # FECHA
        # =====================================================

        df["FechaHora"] = pd.to_datetime(
            df["FechaHora"],
            dayfirst=True
        )

        # =====================================================
        # NUMÉRICOS
        # =====================================================

        df["Valor"] = (
            df["Valor"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        # =====================================================
        # ORDEN
        # =====================================================

        df = df.sort_values("FechaHora")

        # =====================================================
        # FILTROS
        # =====================================================

        p1 = df[df["Variable"] == "P1"].copy()
        p2 = df[df["Variable"] == "P2"].copy()
        q = df[df["Variable"] == "Q"].copy()

        # =====================================================
        # PROMEDIOS
        # =====================================================

        p1_promedio = p1["Valor"].mean()
        p2_promedio = p2["Valor"].mean()
        q_promedio = q["Valor"].mean()

        # =====================================================
        # DELTA T
        # =====================================================

        q["Delta_t_s"] = (
            q["FechaHora"]
            .diff()
            .dt.total_seconds()
        )

        q["Delta_t_s"] = q["Delta_t_s"].fillna(0)

        # =====================================================
        # VOLUMEN
        # =====================================================

        q["Volumen_m3"] = (
            q["Valor"] * q["Delta_t_s"]
        ) / 1000

        volumen_total = q["Volumen_m3"].sum()

        # =====================================================
        # MNF
        # =====================================================

        q["Hora"] = q["FechaHora"].dt.hour

        q_noche = q[
            (q["Hora"] >= 2) &
            (q["Hora"] < 4)
        ].copy()

        if not q_noche.empty:

            q_noche = q_noche.sort_values("FechaHora")

            intervalo_min = (
                q_noche["FechaHora"]
                .diff()
                .dt.total_seconds()
                .median()
            ) / 60

            muestras_60min = max(
                1,
                int(60 / intervalo_min)
            )

            q_noche["Rolling_MNF"] = (
                q_noche["Valor"]
                .rolling(
                    window=muestras_60min,
                    min_periods=1
                )
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

        col1.metric(
            "P. aguas arriba",
            f"{p1_promedio:.2f} bar"
        )

        col2.metric(
            "P. aguas abajo",
            f"{p2_promedio:.2f} bar"
        )

        col3.metric(
            "Q promedio",
            f"{q_promedio:.2f} lps"
        )

        col4.metric(
            "Volumen total",
            f"{volumen_total:.1f} m³"
        )

        if nmf is not None:

            col5.metric(
                "MNF",
                f"{nmf:.2f} lps"
            )

        # =====================================================
        # LAYOUT
        # =====================================================

        col_izq, col_der = st.columns([1, 2.3])

        # =====================================================
        # IZQUIERDA
        # =====================================================

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
                    round(p1_promedio, 2),
                    round(p2_promedio, 2),
                    round(q_promedio, 2),
                    round(volumen_total, 2),
                    round(nmf, 2) if nmf is not None else "-"
                ],

                "Unidad": [
                    "bar",
                    "bar",
                    "lps",
                    "m³",
                    "lps"
                ]
            })

            st.dataframe(
                resultado,
                use_container_width=True,
                height=230
            )

            if hora_nmf is not None:

                st.success(
                    f"""
                    🌙 MNF detectado
                    
                    Hora:
                    {hora_nmf.strftime('%d/%m/%Y %H:%M')}
                    
                    Valor:
                    {nmf:.2f} lps
                    """
                )

        # =====================================================
        # DERECHA
        # =====================================================

        with col_der:

            st.subheader("📉 Serie temporal de caudal")

            fig = go.Figure()

            # =====================================================
            # CAUDAL
            # =====================================================

            fig.add_trace(

                go.Scatter(
                    x=q["FechaHora"],
                    y=q["Valor"],
                    mode="lines",
                    name="Caudal",
                    line=dict(width=2)
                )
            )

            # =====================================================
            # LÍNEA MNF
            # =====================================================

            if nmf is not None:

                fig.add_hline(
                    y=nmf,
                    line_dash="dash",
                    annotation_text=f"MNF = {nmf:.2f} lps",
                    annotation_position="top left"
                )

            # =====================================================
            # LÍMITES EJE Y
            # =====================================================

            y_min = q["Valor"].min() * 0.9
            y_max = q["Valor"].max() * 1.1

            # =====================================================
            # CONFIGURACIÓN GRÁFICA
            # =====================================================

            fig.update_layout(

                height=470,

                margin=dict(
                    l=10,
                    r=10,
                    t=40,
                    b=10
                ),

                xaxis_title="Fecha y hora",
                yaxis_title="Caudal (lps)",

                hovermode="x unified",

                xaxis=dict(
                    rangeslider=dict(visible=True),
                    fixedrange=False
                ),

                yaxis=dict(
                    fixedrange=True,
                    range=[y_min, y_max]
                ),

                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =====================================================
        # DESCARGA
        # =====================================================

        csv = resultado.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Descargar resumen",
            data=csv,
            file_name="Resumen_Dashboard_CEA.csv",
            mime="text/csv"
        )
