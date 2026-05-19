import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="CEA Dashboard",
    layout="wide"
)

# =====================================================
# TÍTULO
# =====================================================

st.title("📊 CEA Datalogger Dashboard")

st.write(
    """
    Dashboard hidráulico para análisis de:
    
    • Presiones promedio  
    • Caudal promedio  
    • Volumen acumulado  
    • MNF / Minimum Night Flow (IWA)
    """
)

# =====================================================
# CARGAR ARCHIVO
# =====================================================

archivo = st.file_uploader(
    "📂 Subir archivo Excel",
    type=["xlsx"]
)

# =====================================================
# MENSAJE INICIAL
# =====================================================

if archivo is None:

    st.info("⬆️ Primero carga un archivo Excel.")

# =====================================================
# EJECUTAR
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
        # RENOMBRAR COLUMNAS
        # =====================================================

        df = df.rename(columns={
            "Data Logger": "Variable",
            "Fecha y hora": "FechaHora",
            "Media": "Valor"
        })

        # =====================================================
        # FECHAS
        # =====================================================

        df["FechaHora"] = pd.to_datetime(
            df["FechaHora"],
            dayfirst=True
        )

        # =====================================================
        # CONVERTIR A NUMÉRICO
        # =====================================================

        df["Valor"] = (
            df["Valor"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        # =====================================================
        # ORDENAR
        # =====================================================

        df = df.sort_values("FechaHora")

        # =====================================================
        # FILTRAR VARIABLES
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
        # MNF / MINIMUM NIGHT FLOW
        # =====================================================
        # Método:
        # promedio móvil mínimo de 60 minutos
        #
        # Ventana:
        # 02:00 - 04:00
        # =====================================================

        q["Hora"] = q["FechaHora"].dt.hour

        q_noche = q[
            (q["Hora"] >= 2) &
            (q["Hora"] < 4)
        ].copy()

        if not q_noche.empty:

            q_noche = q_noche.sort_values("FechaHora")

            # =====================================================
            # INTERVALO DE MUESTREO
            # =====================================================

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

            # =====================================================
            # PROMEDIO MÓVIL
            # =====================================================

            q_noche["Rolling_MNF"] = (
                q_noche["Valor"]
                .rolling(
                    window=muestras_60min,
                    min_periods=1
                )
                .mean()
            )

            # =====================================================
            # OBTENER MNF
            # =====================================================

            idx_nmf = q_noche["Rolling_MNF"].idxmin()

            nmf = q_noche.loc[idx_nmf, "Rolling_MNF"]

            hora_nmf = q_noche.loc[idx_nmf, "FechaHora"]

        else:

            nmf = None
            hora_nmf = None

        # =====================================================
        # KPI VISUALES
        # =====================================================

        st.divider()

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "P1 promedio",
            f"{p1_promedio:.2f} bar"
        )

        col2.metric(
            "P2 promedio",
            f"{p2_promedio:.2f} bar"
        )

        col3.metric(
            "Q promedio",
            f"{q_promedio:.2f} lps"
        )

        col4.metric(
            "Volumen",
            f"{volumen_total:.1f} m³"
        )

        if nmf is not None:

            col5.metric(
                "MNF",
                f"{nmf:.2f} lps"
            )

        # =====================================================
        # LAYOUT PRINCIPAL
        # =====================================================

        col_izq, col_der = st.columns([1, 2.2])

        # =====================================================
        # COLUMNA IZQUIERDA
        # =====================================================

        with col_izq:

            st.subheader("📋 Resumen")

            resultado = pd.DataFrame({

                "Indicador": [
                    "P1 promedio",
                    "P2 promedio",
                    "Q promedio",
                    "Volumen acumulado",
                    "MNF (IWA)"
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
                height=250
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
        # COLUMNA DERECHA
        # =====================================================

        with col_der:

            st.subheader("📉 Serie temporal de caudal")

            fig = go.Figure()

            # =====================================================
            # LÍNEA CAUDAL
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

                height=500,

                margin=dict(
                    l=20,
                    r=20,
                    t=40,
                    b=20
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

        st.divider()

        csv = resultado.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Descargar resumen",
            data=csv,
            file_name="Resumen_Datalogger.csv",
            mime="text/csv"
        )