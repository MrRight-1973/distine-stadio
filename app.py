import streamlit as st
import io
import qrcode
import pandas as pd
from estrattore import analizza_distinta
from creatore_pdf import genera_pdf
from utils import pulisci_testo

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara Gestionale")
st.write("Carica i fogli gara ed effettua modifiche o slittamenti istantanei sulle liste.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

if "griglia_casa" not in st.session_state:
    st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
if "griglia_ospite" not in st.session_state:
    st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")

col_f1, col_f2 = st.columns(2)
with col_f1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
with col_f2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")

if file_casa and file_ospite:
    if "dati_mappati" not in st.session_state:
        if st.button("🔍 Fase 1: Esegui Scansione AI delle Immagini", type="primary"):
            with st.spinner("L'AI sta leggendo le distinte..."):
                try:
                    casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
                    ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                    
                    st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                    st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                    st.session_state["macro_info"] = {
                        "campionato": casa_raw["campionato"], 
                        "data": casa_raw["data"], 
                        "squadra_casa": casa_raw["squadra"], 
                        "all_casa": casa_raw["allenatore"], 
                        "squadra_ospite": ospite_raw["squadra"], 
                        "all_ospite": ospite_raw["allenatore"]
                    }
                    st.session_state["dati_mappati"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante l'analisi visiva: {e}")

if "dati_mappati" in st.session_state:
    st.markdown("---")
    st.header("✏️ Fase 2: Controllo, Correzione e Funzioni di Shift")
    
    info = st.session_state["macro_info"]
    
    st.subheader("🏁 Informazioni Generali Match")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        edit_campionato = st.text_input("🏆 Campionato / Categoria", value=info["campionato"])
        edit_arbitro = st.text_input("🏁 Arbitro (Nome e Cognome)", value="")
        edit_ass1 = st.text_input("🚩 Assistente 1", value="")
    with c_g2:
        edit_data = st.text_input("📅 Data Partita", value=info["data"])
        st.write("")
        edit_ass2 = st.text_input("🚩 Assistente 2", value="")
        
    st.markdown("---")
    
    c_sq1, c_sq2 = st.columns(2)
    opzioni_righe = [i for i in range(1, 21)]
    
    # --- GESTIONE SQUADRA CASA ---
    with c_sq1:
        st.subheader("🏠 SQUADRA CASA")
        edit_nome_casa = st.text_input("Nome Società Ospitante", value=info["squadra_casa"])
        edit_all_casa = st.text_input("Allenatore Ospitante", value=info["all_casa"])
        
        st.session_state["griglia_casa"] = st.data_editor(st.session_state["griglia_casa"], key="editor_casa_current", use_container_width=True)
        
        c_ctrl_c1, c_ctrl_c2 = st.columns([1, 1])
        with c_ctrl_c1:
            riga_scelta_casa = st.selectbox("🎯 Riga (Casa)", options=opzioni_righe, index=12, key="sel_casa")
        with c_ctrl_c2:
            st.write(" <div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("⬇️", key="shift_down_casa", use_container_width=True, help="Slitta in basso"):
                    df = st.session_state["griglia_casa"].copy().reset_index()
                    idx = riga_scelta_casa - 1
                    nuova_riga = pd.DataFrame([{"N°": riga_scelta_casa, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], nuova_riga, df.iloc[idx:19]]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_casa"] = df_nuovo.set_index("N°")
                    st.rerun()
            with c_btn2:
                if st.button("⬆️", key="shift_up_casa", use_container_width=True, help="Slitta in alto"):
                    df = st.session_state["griglia_casa"].copy().reset_index()
                    idx = riga_scelta_casa - 1
                    riga_vuota_finale = pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], riga_vuota_finale]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_casa"] = df_nuovo.set_index("N°")
                    st.rerun()

    # --- GESTIONE SQUADRA OSPITE ---
    with c_sq2:
        st.subheader("🚀 SQUADRA OSPITE")
        edit_nome_ospite = st.text_input("Nome Società Ospite", value=info["squadra_ospite"])
        edit_all_ospite = st.text_input("Allenatore Ospite", value=info["all_ospite"])
        
        st.session_state["griglia_ospite"] = st.data_editor(st.session_state["griglia_ospite"], key="editor_ospite_current", use_container_width=True)
        
        c_ctrl_o1, c_ctrl_o2 = st.columns([1, 1])
        with c_ctrl_o1:
            riga_scelta_ospite = st.selectbox("🎯 Riga (Ospite)", options=opzioni_righe, index=12, key="sel_ospite")
        with c_ctrl_o2:
            st.write(" <div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
            o_btn1, o_btn2 = st.columns(2)
            with o_btn1:
                if st.button("⬇️", key="shift_down_ospite", use_container_width=True, help="Slitta in basso"):
                    df = st.session_state["griglia_ospite"].copy().reset_index()
                    idx = riga_scelta_ospite - 1
                    nuova_riga = pd.DataFrame([{"N°": riga_scelta_ospite, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], nuova_riga, df.iloc[idx:19]]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_ospite"] = df_nuovo.set_index("N°")
                    st.rerun()
            with o_btn2:
                if st.button("⬆️", key="shift_up_ospite", use_container_width=True, help="Slitta in alto"):
                    df = st.session_state["griglia_ospite"].copy().reset_index()
                    idx = riga_scelta_ospite - 1
                    riga_vuota_finale = pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], riga_vuota_finale]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_ospite"] = df_nuovo.set_index("N°")
                    st.rerun()

    # --- GENERAZIONE PDF FINALE ---
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code", type="primary"):
        with st.spinner("Generazione del foglio di gara e caricamento su Google Drive..."):
            try:
                import datetime
                import requests
                import json
                import io
                import qrcode
                from google.oauth2 import service_account
                import google.auth.transport.requests

                giocatori_casa_salvati = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
                giocatori_ospite_salvati = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
                
                squadra_casa_corretta = {
                    "squadra": pulisci_testo(edit_nome_casa),
                    "allenatore": pulisci_testo(edit_all_casa),
                    "giocatori": giocatori_casa_salvati
                }
                squadra_ospite_corretta = {
                    "squadra": pulisci_testo(edit_nome_ospite),
                    "allenatore": pulisci_testo(edit_all_ospite),
                    "giocatori": giocatori_ospite_salvati
                }
                info_gara_corrette = {
                    "campionato": pulisci_testo(edit_campionato),
                    "data": pulisci_testo(edit_data),
                    "arbitro": pulisci_testo(edit_arbitro),
                    "assistente1": pulisci_testo(edit_ass1),
                    "assistente2": pulisci_testo(edit_ass2)
                }
                
                # 1. Recupero parametri dai Secrets
                folder_id = st.secrets.get("DRIVE_FOLDER_ID")
                client_email = st.secrets.get("DRIVE_CLIENT_EMAIL")
                project_id = st.secrets.get("DRIVE_PROJECT_ID")
                private_key = st.secrets.get("DRIVE_PRIVATE_KEY")
                
                if not all([folder_id, client_email, project_id, private_key]):
                    st.error("Configurazione dei parametri di Drive incompleta nei Secrets!")
                    st.stop()

                # 2. Struttura del dizionario forzata con TUTTI gli endpoint richiesti per azzerare i fallback 404
                info_creds = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key_id": "74446930d14900f6eab6bd3ff13bb44dcc9ec4c9",
                    "private_key": private_key,
                    "client_email": client_email,
                    "client_id": "106839468953031910546",
                    "auth_uri": "https://google.com",
                    "token_uri": "https://googleapis.com",
                    "auth_provider_x509_cert_url": "https://googleapis.com",
                    "client_x509_cert_url": f"https://googleapis.com{client_email.replace('@', '%40')}"
                }
                
                scopes = ['https://googleapis.com']
                creds = service_account.Credentials.from_service_account_info(info_creds, scopes=scopes)
                
                # Usiamo l'oggetto Request standard per validare e richiedere il token in sicurezza
                richiesta_trasporto = google.auth.transport.requests.Request()
                creds.refresh(richiesta_trasporto)
                access_token = creds.token
                
                if not access_token:
                    st.error("Impossibile recuperare il token di accesso dai server di autenticazione Google.")
                    st.stop()
                
                headers_auth = {"Authorization": f"Bearer {access_token}"}

                # 3. Prepariamo i metadati del file unico
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_societa = pulisci_testo(edit_nome_casa).replace(" ", "_")
                nome_file_pdf = f"distinta_{nome_societa}_{timestamp}.pdf"

                # 4. Generiamo il PDF temporaneo iniziale (senza QR definitivo)
                pdf_temporaneo_bytes = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_code_bytes=None)
                
                # 5. Caricamento iniziale su Google Drive tramite chiamata multipart nativa REST v3
                metadata = {
                    'name': nome_file_pdf,
                    'parents': [folder_id]
                }
                files = {
                    'data': (None, json.dumps(metadata), 'application/json; charset=UTF-8'),
                    'file': (nome_file_pdf, pdf_temporaneo_bytes, 'application/pdf')
                }
                
                r_upload = requests.post(
                    'https://googleapis.com',
                    headers=headers_auth,
                    files=files
                )
                
                if r_upload.status_code != 200:
                    st.error(f"Errore durante l'upload iniziale su Drive: {r_upload.text}")
                    st.stop()
                    
                file_id = r_upload.json().get("id")
                
                # 6. Cambiamo i permessi del file per renderlo pubblico (Lettore per chiunque abbia il link)
                perm_url = f"https://googleapis.com{file_id}/permissions"
                r_perm = requests.post(perm_url, headers=headers_auth, json={'role': 'reader', 'type': 'anyone'})
                
                if r_perm.status_code != 200:
                    st.error(f"Impossibile impostare i permessi di condivisione su Drive: {r_perm.text}")
                    st.stop()
                
                # 7. Costruiamo il link diretto per lo smartphone
                pdf_url = f"https://google.com{file_id}"
                
                # 8. Generiamo il QR Code reale associato a questo link
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
                qr.add_data(pdf_url)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                buf_qr = io.BytesIO()
                img_qr.save(buf_qr, format="PNG")
                qr_bytes = buf_qr.getvalue()
                
                # 9. Rigeneriamo il PDF completo includendo il QR Code reale stampato sopra
                pdf_finale_bytes = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_bytes)
                
                # 10. Aggiorniamo il file su Google Drive inserendo la versione con il QR Code definitivo
                update_url = f"https://googleapis.com{file_id}?uploadType=media"
                headers_update = headers_auth.copy()
                headers_update["Content-Type"] = "application/pdf"
                
                r_update = requests.patch(update_url, headers=headers_update, data=pdf_finale_bytes)
                
                if r_update.status_code != 200:
                    st.error(f"Errore durante l'aggiornamento finale del PDF: {r_update.text}")
                    st.stop()
                
                # Salvataggio nello stato dell'applicazione
                st.session_state["pdf_interattivo_pronto"] = pdf_finale_bytes
                st.session_state["pdf_url_condiviso"] = pdf_url
                st.success("🎉 Distinta salvata su Google Drive e QR Code sincronizzato!")
                
            except Exception as ex:
                st.error(f"Si è verificato un errore durante la compilazione finale: {ex}")
