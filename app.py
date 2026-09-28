import streamlit as st
import io
import qrcode
import requests
import base64
from estrattore import analizza_distinta, genera_pdf

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara")
st.write("Carica le distinte di entrambe le squadre per generare il PDF unico A4 con QR Code.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

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
                    dati_casa = analizza_distinta(file_casa, "CASA", api_key_openai)
                    dati_ospite = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                    
                    pdf_data = genera_pdf(dati_casa, dati_ospite)
                    st.success("🎉 Distinte elaborate ed unite con successo!")
                    
                    # Caricamento cloud temporaneo con gestione fallimenti integrata
                    pdf_url = None
                    try:
                        files = {'file': ('riepilogo_distinte.pdf', pdf_data, 'application/pdf')}
                        response_cloud = requests.post('https://file.io', files=files, timeout=5)
                        if response_cloud.status_code == 200:
                            pdf_url = response_cloud.json().get("link")
                    except Exception:
                        pdf_url = None

                    # Failsafe locale se file.io non risponde
                    if not pdf_url:
                        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                        pdf_url = f"data:application/pdf;base64,{b64_pdf}"
                        st.info("💡 Nota: Generazione QR Code eseguita in modalità locale senza server esterni.")

                    # Layout dei risultati
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 📋 Riepilogo Squadre")
                        st.write(f"**⚽ Gara:** {dati_casa['squadra']} vs {dati_ospite['squadra']}")
                        st.write(f"**🏠 Allenatore Casa:** {dati_casa['allenatore']}")
                        st.write(f"**🚀 Allenatore Ospite:** {dati_ospite['allenatore']}")
                        st.write("")
                        
                        st.download_button(
                            label="💾 Scarica PDF su questo PC",
                            data=pdf_data,
                            file_name="riepilogo_distinte.pdf",
                            mime="application/pdf"
                        )
                    
                    with c2:
                        st.markdown("### 📱 Scarica su Smartphone")
                        st.write("Inquadra questo QR Code con il telefono per salvare il PDF:")
                        
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
                        
                        if not pdf_url.startswith("data:"):
                            st.caption(f"Link diretto temporaneo: {pdf_url}")
                        
                except Exception as e:
                    st.error(f"Si è verificato un errore durante l'elaborazione dei file: {e}")
