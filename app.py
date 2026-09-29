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
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

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
                
                # 1. Autenticazione con Google Drive tramite Secrets
                creds_dict = st.secrets["google_credentials"]
                folder_id = st.secrets.get("DRIVE_FOLDER_ID")
                
                if not creds_dict or not folder_id:
                    st.error("Credenziali Google o DRIVE_FOLDER_ID non trovati nei configuratori secrets!")
                    st.stop()
                    
                creds = service_account.Credentials.from_service_account_info(creds_dict)
                drive_service = build('drive', 'v3', credentials=creds)
                
                # Nome del file unico basato sul tempo
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_societa = pulisci_testo(edit_nome_casa).replace(" ", "_")
                nome_file_pdf = f"distinta_{nome_societa}_{timestamp}.pdf"

                # 2. Generiamo il PDF temporaneo iniziale (senza QR definitivo)
                pdf_temporaneo_bytes = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_code_bytes=None)
                
                # 3. Primo caricamento del file grezzo su Google Drive per assicurarci un ID file univoco
                file_metadata = {
                    'name': nome_file_pdf,
                    'parents': [folder_id]
                }
                media = MediaIoBaseUpload(io.BytesIO(pdf_temporaneo_bytes), mimetype='application/pdf', resumable=True)
                file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                file_id = file_drive.get('id')
                
                # 4. Cambiamo i permessi del file per renderlo leggibile a chiunque abbia il link (necessario per il QR Code)
                permission_metadata = {
                    'type': 'anyone',
                    'role': 'reader'
                }
                drive_service.permissions().create(fileId=file_id, body=permission_metadata).execute()
                
                # 5. Costruiamo il link diretto per la visualizzazione/anteprima immediata del PDF su Smartphone
                # Rispetto al classico 'view', l'endpoint 'uc?id=' forza la visualizzazione pulita senza l'interfaccia di Drive
                pdf_url = f"https://google.com{file_id}"
                
                # 6. Generiamo il QR Code reale associato a questo indirizzo di Google Drive
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
                qr.add_data(pdf_url)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                buf_qr = io.BytesIO()
                img_qr.save(buf_qr, format="PNG")
                qr_bytes = buf_qr.getvalue()
                
                # 7. Rigeneriamo il PDF completo includendo il QR Code stampato sopra
                pdf_finale_bytes = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_bytes)
                
                # 8. Aggiorniamo il file precedentemente creato su Google Drive inserendo la versione con il QR Code funzionante
                media_aggiornato = MediaIoBaseUpload(io.BytesIO(pdf_finale_bytes), mimetype='application/pdf', resumable=True)
                drive_service.files().update(fileId=file_id, media_body=media_aggiornato).execute()
                
                # Salvataggio nello stato dell'applicazione
                st.session_state["pdf_interattivo_pronto"] = pdf_finale_bytes
                st.session_state["pdf_url_condiviso"] = pdf_url
                st.success("🎉 Distinta salvata su Google Drive e QR Code sincronizzato!")
                
            except Exception as ex:
                st.error(f"Si è verificato un errore durante la compilazione finale: {ex}")
