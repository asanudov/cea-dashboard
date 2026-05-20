# =====================================================
# SIDEBAR (CLEAN FIX)
# =====================================================

with st.sidebar:

    st.image("logo.png", width=160)

    st.markdown("## Dashboard hidráulico")

    st.markdown("""
Este dashboard permite:

- Analizar presiones (P1 / P2)
- Caudal promedio
- Volumen total
- MNF (Minimum Night Flow)
- Detectar tandeo
""")

    # 🔥 FIX CSS LOCAL SOLO PARA SIDEBAR UPLOADER
    st.markdown("""
    <style>

    /* QUITAR TEXTO DE INSTRUCCIONES */
    section[data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }

    /* QUITAR ICONO keyboard_double / SVG INTERNOS */
    section[data-testid="stFileUploader"] svg {
        display: none !important;
    }

    /* LIMPIAR LABELS INTERNOS */
    section[data-testid="stFileUploader"] label {
        display: none !important;
    }

    </style>
    """, unsafe_allow_html=True)

    archivo = st.file_uploader(
        label="",
        type=["xlsx"],
        label_visibility="collapsed"
    )

    st.caption("📂 Cargar archivo Excel")
