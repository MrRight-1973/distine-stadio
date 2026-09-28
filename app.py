import streamlit as st
import io
import qrcode
import requests
import pandas as pd
from estrattore import analizza_distinta, genera_pdf, pulisci_testo

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara Interattivo")
st.write("Carica i fogli gara, modifica o correggi a mano i dati estratti dall'AI, e genera il PDF A4 con QR Code integrato.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

# 1. Caricamento file iniziale
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
with col_f2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")

# Sezione di elaborazione AI iniziale
if file_casa and file_ospite:
    if "dati_iniziali_estratti" not in st.session_state:
        if st.button("🔍 Fase 1: Esegui Scansione AI delle Immagini", type="primary"):
            with st.spinner("L'AI sta leggendo le distinte..."):
                try:
                    casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
                    ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                    st.session_state["dati_iniziali_estratti"] = {"casa": casa_raw, "ospite": ospite_raw}
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante l'analisi visiva: {e}")

# --- AREA DI CORREZIONE MANUALE A SCHERMO ---
if "dati_iniziali_estratti" in st.session_state:
    st.markdown("---")
    st.header("✏️ Fase 2: Controllo e Correzione Manuale dei Dati")
    st.info("Clicca sulle caselle di testo o sulle tabelle qui sotto per modificare o correggere a mano eventuali nomi, anni o scritte prima di salvare.")
    
    casa_data = st.session_state["dati_iniziali_estratti"]["casa"]
    ospite_data = st.session_state["dati_iniziali_estratti"]["ospite"]
    
    # Intestazione Arbitri e Gara
    st.subheader("🏁 Informazioni Generali Match")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        edit_campionato = st.text_input("🏆 Campionato / Categoria", value=casa_data.get("campionato", ""))
        edit_arbitro = st.text_input("🏁 Arbitro (Nome e Cognome)", value="")
        edit_ass1 = st.text_input("🚩 Assistente 1", value="")
    with c_g2:
        edit_data = st.text_input("📅 Data Partita", value=casa_data.get("data", ""))
        st.write("")
        edit_ass2 = st.text_input("🚩 Assistente 2", value="")
        
    st.markdown("---")
    
    # Sezione Squadre ed Editor Tabelle Giocatori
    c_sq1, c_sq2 = st.columns(2)
    
    with c_sq1:
        st.subheader("🏠 Modifica Dati SQUADRA CASA")
        edit_nome_casa = st.text_input("Nome Società Ospitante", value=casa_data.get("squadra", ""))
        edit_all_casa = st.text_input("Allenatore Ospitante", value=casa_data.get("allenatore", ""))
        
        # Converte la lista giocatori in un DataFrame Pandas per renderlo editabile in una griglia tipo Excel
        df_casa = pd.DataFrame(casa_data.get("giocatori", []))
        if df_casa.empty:
            df_casa = pd.DataFrame(columns=["numero", "cognome_nome", "anno_nascita"])
        st.write("📋 Lista Calciatori (Fai doppio clic su una cella per modificarla):")
        editor_casa = st.data_editor(df_casa, num_rows="dynamic", key="edit_grid_casa", use_container_width=True)
        
    with c_sq2:
        st.subheader("🚀 Modifica Dati SQUADRA OSPITE")
        edit_nome_ospite = st.text_input("Nome Società Ospite", value=ospite_data.get("squadra", ""))
        edit_all_ospite = st.text_input("Allenatore Ospite", value=ospite_data.get("allenatore", ""))
        
        df_ospite = pd.DataFrame(ospite_data.get("giocatori", []))
        if df_ospite.empty:
            df_ospite = pd.DataFrame(columns=["numero", "cognome_nome", "anno_nascita"])
        st.write("📋 Lista Calciatori (Fai doppio clic su una cella per modificarla):")
        editor_ospite = st.data_editor(df_ospite, num_rows="dynamic", key="edit_grid_ospite", use_container_width=True)

    # --- GENERAZIONE FINALE PDF CON QR CODE STAMPATO ---
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code", type="primary"):
        with st.spinner("Generazione del foglio di gara A4 definitivo..."):
            try:
                # Ricostruzione dei dizionari applicando le modifiche manuali dell'utente
                squadra_casa_corretta = {
                    "squadra": pulisci_testo(edit_nome_casa),
                    "allenatore": pulisci_testo(edit_all_casa),
                    "giocatori": editor_casa.to_dict(orient="records")
                }
                squadra_ospite_corretta = {
                    "squadra": pulisci_testo(edit_nome_ospite),
                    "allenatore": pulisci_testo(edit_all_ospite),
                    "giocatori": editor_ospite.to_dict(orient="records")
                }
                info_gara_corrette = {
                    "campionato": pulisci_testo(edit_campionato),
                    "data": pulisci_testo(edit_data),
                    "arbitro": pulisci_testo(edit_arbitro),
                    "assistente1": pulisci_testo(edit_ass1),
                    "assistente2": pulisci_testo(edit_ass2)
                }
                
                # Definiamo l'URL della Web App per il QR code
                pdf_url = "https://streamlit.io"
                
                # Generiamo i byte fisici del QR Code
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
                qr.add_data(pdf_url)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                buf_qr = io.BytesIO()
                img_qr.save(buf_qr, format="PNG")
                qr_bytes = buf_qr.getvalue()
                
                # Generiamo il PDF A4 passando i dati corretti a mano e i byte del QR Code stampabile
                pdf_finale = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_bytes)
                st.session_state["pdf_interattivo_pronto"] = pdf_finale
                st.success("🎉 Documento A4 unificato e QR Code pronti per il download!")
                
            except Exception as ex:
                st.error(f"Si è verificato un errore durante la compilazione finale: {ex}")

# Pulsanti di salvataggio finale
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
