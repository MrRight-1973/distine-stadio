import streamlit as st

def svuota_scansione():
    """Cancella i dati mappati per consentire una nuova lettura pulita"""
    if "dati_mappati" in st.session_state:
        del st.session_state["dati_mappati"]
    if "pdf_interattivo_pronto" in st.session_state:
        del st.session_state["pdf_interattivo_pronto"]
    st.rerun()

def render_info_match(info):
    """Mostra i campi di input della terna arbitrale e informazioni gara"""
    st.subheader("🏁 Informazioni Generali Match (Terna Ufficiale)")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        campionato = st.text_input("🏆 Campionato / Categoria", value=info["campionato"])
        arbitro = st.text_input("🏁 Arbitro (Nome e Cognome)", value="")
        ass1 = st.text_input("🚩 Assistente Arbitrale 1", value="")
    with c_g2:
        data = st.text_input("📅 Data Partita", value=info["data"])
        st.write("")
        ass2 = st.text_input("🚩 Assistente Arbitrale 2", value="")
    return {"campionato": campionato, "data": data, "arbitro": arbitro, "assistente1": ass1, "assistente2": ass2}

def render_download_buttons():
    """Mostra i pulsanti per scaricare il PDF generato sia su desktop che mobile"""
    if "pdf_interattivo_pronto" in st.session_state:
        st.write("")
        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button(
                label="💾 Scarica PDF per il Computer",
                data=st.session_state["pdf_interattivo_pronto"],
                file_name="distinta_ufficiale_A4.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with c_dl2:
            st.download_button(
                label="📥 Scarica PDF su Smartphone",
                data=st.session_state["pdf_interattivo_pronto"],
                file_name="distinta_ufficiale_A4_mobile.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
