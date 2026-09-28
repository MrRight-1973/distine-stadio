import streamlit as st
import io
import qrcode
import requests
import base64
from estrattore import analizza_distinta, genera_pdf

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara")
st.write("Carica le distinte, compila i dati della terna e genera il PDF unico A4 con QR Code.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

# --- NUOVA SEZIONE: PUNTO 2 (DATI DELLA GARA COMPILABILI) ---
st.markdown("### 📝 Dati della Gara ed Arbitri")
st.write("I campi Campionato e Data verranno letti in automatico dall'AI, ma puoi sovrascriverli o correggerli qui sotto se necessario.")

c_info1, c_info2 = st.columns(2)
with c_info1:
    input_campionato = st.text_input("🏆 Campionato / Categoria (es. PROMOZIONE)", value="")
    input_arbitro = st.text_input("🏁 Nome dell'Arbitro", value="")
    input_assistente1 = st.text_input("🚩 Assistente 1 (Guardalinee)", value="")

with c_info2:
    input_data = st.text_input("📅 Data della Partita (es. 28/09/2026)", value="")
    st.write("") # Spaziatore grafico
    input_assistente2 = st.text_input("🚩 Assistente 2 (Guardalinee)", value="")

st.markdown("---")

# 2. Interfaccia grafica a due colonne per il caricamento file
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
    if file_casa:
        st.image(file_casa, use_container_width=True)

with col2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")
    if file_ospite:
        st.image(file_ospite, use_container_width=True)

# 3. Blocco di attivazione ed elaborazione
if file_casa and file_ospite:
    st.write("")
    if st.button("⚡ Elabora e Genera PDF con QR Code", type="primary"):
        if not api_key_openai:
            st.error("🚨 Chiave API non trovata! Inserisci la stringa 'OPENAI_API_KEY' nei 'Secrets' di Streamlit Cloud.")
        else:
            with st.spinner("Estrazione dati e creazione PDF in corso..."):
                try:
                    # Estrazione e formattazione con AI
                    dati_casa = analizza_distinta(file_casa, "CASA", api_key_openai)
                    dati_ospite = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                    
                    # Raggruppamento delle informazioni extra inserite dall'utente
                    info_gara = {
                        "campionato": input_campionato if input_campionato else dati_casa.get("campionato", "NON INDICATO"),
                        "data": input_data if input_data else dati_casa.get("data", "NON INDICATA"),
                        "arbitro": input_arbitro if input_arbitro else "NON INDICATO",
                        "assistente1": input_assistente1 if input_assistente1 else "NON INDICATO",
                        "assistente2": input_assistente2 if input_assistente2 else "NON INDICATO"
                    }
                    
                    # Generazione PDF A4 con intestazione completa
                    pdf_data = genera_pdf(dati_casa, dati_ospite, info_gara)
                    st.session_state["pdf_pronto"] = pdf_data
                    st.success("🎉 Distinte elaborate ed unite con successo!")
                    
                    # Caricamento cloud temporaneo su file.io
                    pdf_url = None
                    try:
                        files = {'file': ('riepilogo_distinte.pdf', pdf_data, 'application/pdf')}
                        response_cloud = requests.post('https://file.io', files=files, timeout=5)
                        if response_cloud.status_code == 200:
                            pdf_url = response_cloud.json().get("link")
                    except Exception:
                        pdf_url = None

                    # Failsafe se file.io non risponde (rimanda alla Web App stessa)
                    if not pdf_url:
                        pdf_url = "https://streamlit.io"
                        st.info("💡 Nota: Il QR Code rimanderà alla pagina web corrente per scaricare il file dal telefono.")

                    # Layout dei risultati visivi a schermo
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 📋 Riepilogo Gara")
                        st.write(f"**🏆 Campionato:** {info_gara['campionato']}")
                        st.write(f"**📅 Data Match:** {info_gara['data']}")
                        st.write(f"**⚽ Gara:** {dati_casa['squadra']} vs {dati_ospite['squadra']}")
                        st.write(f"**🏠 Allenatore Casa:** {dati_casa['allenatore']}")
                        st.write(f"**🚀 Allenatore Ospite:** {dati_ospite['allenatore']}")
                        st.write(f"**🏁 Arbitro:** {info_gara['arbitro']}")
                        st.write("")
                        
                        st.download_button(
                            label="💾 Scarica PDF su questo PC",
                            data=pdf_data,
                            file_name="riepilogo_distinte.pdf",
                            mime="application/pdf"
                        )
                    
                    with c2:
                        st.markdown("### 📱 Scarica su Smartphone")
                        st.write("Inquadra questo QR Code con il telefono per scaricare il documento:")
                        
                        qr = qrcode.QRCode(
                            version=None,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=10,
                            border=4
                        )
                        qr.add_data(pdf_url)
                        qr.make(fit=True)
                        img_qr = qr.make_image(fill_color="black", back_color="white")
                        
                        io_buf_qr = io.BytesIO()
                        img_qr.save(io_buf_qr, format="PNG")
                        st.image(io_buf_qr.getvalue(), width=220)
                        
                        if not pdf_url.startswith("https://streamlit.io"):
                            st.caption(f"Link diretto temporaneo: {pdf_url}")
                        
                except Exception as e:
                    st.error(f"Si è verificato un errore durante l'elaborazione dei file: {e}")

# Pulsante di scaricamento per dispositivi mobili
if "pdf_pronto" in st.session_state:
    st.markdown("---")
    st.subheader("📲 Area Download Smartphone")
    st.download_button(
        label="📥 Premi qui per salvare il PDF sul tuo Telefono",
        data=st.session_state["pdf_pronto"],
        file_name="riepilogo_distinte_mobile.pdf",
        mime="application/pdf",
        type="primary"
    )
