import streamlit as st
import io
import qrcode
import pandas as pd
from estrattore import analizza_distinta
from creatore_pdf import genera_pdf
from utils import pulisci_testo

# --- CONTROLLO ACCESSO DA QR CODE SMARTPHONE ---
from pagine_web import mostra_pagina_formazione
mostra_pagina_formazione() 
# Se l'utente ha scansionato il QR, questa funzione si attiva e mostra solo la formazione, ignorando il pannello di gestione.

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
                    
                    # 1. Sovrascriviamo le griglie con i nuovi giocatori estratti
                    st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                    st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                    
                    # 2. Aggiorniamo le macro informazioni generali del match
                    st.session_state["macro_info"] = {
                        "campionato": casa_raw["campionato"], 
                        "data": casa_raw["data"], 
                        "squadra_casa": casa_raw["squadra"], 
                        "all_casa": casa_raw["allenatore"], 
                        "squadra_ospite": ospite_raw["squadra"], 
                        "all_ospite": ospite_raw["allenatore"]
                    }
                    
                    # --- CORREZIONE CRITICA CONTRO IL BLOCCO DEI DATI ---
                    # Eliminiamo i vecchi stati dei widget di testo per costringere Streamlit
                    # a ricaricare a schermo i nuovi nomi appena estratti dall'AI
                    chiavi_da_resettare = ["editor_casa_current", "editor_ospite_current"]
                    for chiave in chiavi_da_resettare:
                        if chiave in st.session_state:
                            st.session_state.pop(chiave)
                    
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

    # --- GENERAZIONE PDF FINALE CON FILE SYSTEM INTERNO (ZERO FILTRI DI SICUREZZA) ---
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code", type="primary"):
        with st.spinner("Salvataggio della formazione nel sistema e ottimizzazione QR..."):
            try:
                import json
                import os
                import secrets
                
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
                
                # Filtriamo le righe vuote dei giocatori
                lista_casa = [[g["N°"], g["GIOCATORE"], g["ANNO"]] for g in giocatori_casa_salvati if str(g["GIOCATORE"]).strip() != ""]
                lista_ospite = [[g["N°"], g["GIOCATORE"], g["ANNO"]] for g in giocatori_ospite_salvati if str(g["GIOCATORE"]).strip() != ""]
                
                pacchetto_match = {
                    "info": [info_gara_corrette["campionato"], info_gara_corrette["data"], info_gara_corrette["arbitro"], info_gara_corrette["assistente1"], info_gara_corrette["assistente2"]],
                    "casa": [squadra_casa_corretta["squadra"], squadra_casa_corretta["allenatore"], lista_casa],
                    "ospite": [squadra_ospite_corretta["squadra"], squadra_ospite_corretta["allenatore"], lista_ospite]
                }
                
                # Generiamo un identificativo cortissimo di 6 lettere per la partita
                id_partita = secrets.token_hex(3)
                
                # Salviamo il file JSON direttamente nella memoria del server Streamlit
                # Creiamo una cartella temporanea se non esiste
                if not os.path.exists("match_data"):
                    os.makedirs("match_data")
                    
                percorso_file = os.path.join("match_data", f"{id_partita}.json")
                with open(percorso_file, "w", encoding="utf-8") as f_out:
                    json.dump(pacchetto_match, f_out)
                
                # URL CORTO E PULITO: I telefoni lo riconosceranno come sicuro al 100%
                pdf_url = f"https://distinte-duecarrare.streamlit.app/"
                
                # Generazione fisica del QR Code ad alta leggibilità
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
                qr.add_data(pdf_url)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                buf_qr = io.BytesIO()
                img_qr.save(buf_qr, format="PNG")
                qr_bytes = buf_qr.getvalue()
                
                # Generazione della distinta PDF finale da stampare
                pdf_finale = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_bytes)
                st.session_state["pdf_interattivo_pronto"] = pdf_finale
                st.session_state["ultimo_qr_link"] = pdf_url
                st.success("🎉 Distinta unificata e QR Code protetto generati!")
                
            except Exception as ex:
                st.error(f"Si è verificato un errore durante la compilazione finale: {ex}")

# --- VISUALIZZAZIONE PULSANTI DI DOWNLOAD DIRETTO ---
if "pdf_interattivo_pronto" in st.session_state:
    st.write("")
    st.markdown("### 💾 Scarica il Documento Compilato")
    
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button(
            label="💻 Scarica PDF per il Computer",
            data=st.session_state["pdf_interattivo_pronto"],
            file_name="distinta_ufficiale_A4.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with c_dl2:
        st.download_button(
            label="📱 Scarica PDF su Smartphone",
            data=st.session_state["pdf_interattivo_pronto"],
            file_name="distinta_ufficiale_A4_mobile.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
# --- ANTEPRIMA VISIVA DEL QR CODE A SCHERMO ---
if "pdf_interattivo_pronto" in st.session_state and "ultimo_qr_link" in st.session_state:
    st.markdown("---")
    st.markdown("### 📱 Anteprima della Pagina Web per Smartphone")
    st.write("Inquadra questo codice con il tuo telefono per verificare la pagina delle formazioni in tempo reale:")
    
    try:
        import io
        import qrcode
        from PIL import Image
        
        # Rigeneriamo rapidamente l'immagine visiva del QR per lo schermo di Streamlit
        qr_display = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
        qr_display.add_data(st.session_state["ultimo_qr_link"])
        qr_display.make(fit=True)
        img_display = qr_display.make_image(fill_color="black", back_color="white")
        
        # Mostriamo l'immagine nativamente con st.image per evitare il crash
        st.image(img_display, caption="QR Code Formazioni - ASD Azzurra Due Carrare", width=250)
        
    except Exception as qr_err:
        st.warning("Anteprima grafica del QR non disponibile a schermo, ma integrata correttamente nel PDF.")
