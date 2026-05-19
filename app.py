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
# ESTILOS
# =====================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Manrope', sans-serif;
    }

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

    h1, h2, h3 {
        font-family: 'Manrope', sans-serif !important;
        font-weight: 700 !important;
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

    st.markdown(
        "<div style='padding-top:25px;'></div>",
        unsafe_allow_html=True
    )

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
# CARGAR ARCHIVOS
# =====================================================

archivos = st.file_uploader(
    "📂 Subir archivos Excel",
    type=["xlsx"],
    accept_multiple_files=True
)

# =====================================================
# MENSAJE INICIAL
# =====================================================

if not archivos:

    st.markdown("""
    ### Calcula automáticamente:
    
    - Presión aguas arriba promedio (bar)
    - Presión aguas abajo promedio (bar)
    - Caudal promedio (lps)
    - Volumen total (m³)
    - MNF (Minimum Night Flow)
    
    ### Además:
    
    - Comparación entre múltiples archivos
    - Comparación de MNF
    - Comparación de caudales
    - Comparación de Q promedio
    - Encendido/apagado de curvas
    """)

    st.info("⬆️ Carga uno o más archivos para comenzar.")

# =====================================================
# EJECUCIÓN
# =====================================================

if archivos:

    ejecutar = st.button("▶ Ejecutar cálculo")

    if ejecutar:

        # =====================================================
        # COLORES
        # =====================================================

        colores = [
            "#1f77b4",
            "#d62728",
            "#2ca02c",
            "#ff7f0e",
            "#9467bd",
            "#17becf"
        ]

        # =====================================================
        # RESULTADOS
        # =====================================================

        resultados = []

        # =====================================================
        # FIGURA
        # =====================================================

        fig = go.Figure()

        # =====================================================
        # TODOS LOS Q
        # =====================================================

        todos_q = []

        # =====================================================
        # LOOP ARCHIVOS
        # =====================================================

        for i, archivo in enumerate(archivos):

            color = colores[i % len(colores)]

            nombre_archivo = archivo.name.replace(".xlsx", "")

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
            # NUMÉRICO
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
            # GUARDAR TODOS LOS Q
            # =====================================================

            todos_q.extend(q["Valor"].tolist())

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

            else:

                nmf = None

            # =====================================================
            # RESULTADOS
            # =====================================================

            resultados.append({

                "Archivo": nombre_archivo,
                "P. aguas arriba": round(p1_promedio, 2),
                "P. aguas abajo": round(p2_promedio, 2),
                "Q promedio": round(q_promedio, 2),
                "Volumen total": round(volumen_total, 2),
                "MNF": round(nmf, 2) if nmf is not None else "-"
            })

            # =====================================================
            # CURVA CAUDAL
            # =====================================================

            fig.add_trace(

                go.Scatter(
                    x=q["FechaHora"],
                    y=q["Valor"],
                    mode="lines",
                    name=f"Q - {nombre_archivo}",
                    line=dict(
                        width=2,
                        color=color
                    )
                )
            )

            # =====================================================
            # LÍNEA Q PROMEDIO
            # =====================================================

            fig.add_trace(

                go.Scatter(
                    x=[q["FechaHora"].min(), q["FechaHora"].max()],
                    y=[q_promedio, q_promedio],
                    mode="lines",
                    name=f"Q Promedio - {nombre_archivo}",
                    line=dict(
                        dash="dot",
                        width=2,
                        color=color
                    )
                )
            )

            # =====================================================
            # LÍNEA MNF
            # =====================================================

            if nmf is not None:

                fig.add_trace(

                    go.Scatter(
                        x=[q["FechaHora"].min(), q["FechaHora"].max()],
                        y=[nmf, nmf],
                        mode="lines",
                        name=f"MNF - {nombre_archivo}",
                        line=dict(
                            dash="dash",
                            width=2,
                            color=color
                        )
                    )
                )

        # =====================================================
        # DATAFRAME RESULTADOS
        # =====================================================

        resultado_df = pd.DataFrame(resultados)

        # =====================================================
        # TABLA
        # =====================================================

        st.divider()

        st.subheader("📋 Resumen comparativo")

        st.dataframe(
            resultado_df,
            use_container_width=True,
            height=250
        )

        # =====================================================
        # GRÁFICA
        # =====================================================

        st.divider()

        st.subheader("📉 Comparación de caudales")

        # =====================================================
        # LÍMITES Y
        # =====================================================

        y_min = min(todos_q) * 0.9
        y_max = max(todos_q) * 1.1

        # =====================================================
        # LAYOUT FIGURA
        # =====================================================

        fig.update_layout(

            height=650,

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

            # =====================================================
            # BLOQUEAR ZOOM VERTICAL
            # =====================================================

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
        # DESCARGAR CSV
        # =====================================================

        csv = resultado_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Descargar resumen comparativo",
            data=csv,
            file_name="Resumen_Comparativo_CEA.csv",
            mime="text/csv"
        )
