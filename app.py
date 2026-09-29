import streamlit as st
import io
import qrcode
import os
import json
import pandas as pd
from estrattore import analizza_distinta
from creatore_pdf import genera_pdf
from utils import pulisci_testo

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

# ==============================================================================
# --- CONTROLLO ACCESSO SMARTPHONE (RETROCOMPATIBILE E BLINDATO) ---
# ==============================================================================
# Strategia di recupero universale per evitare l'AttributeError sulle vecchie versioni di Streamlit
params = {}
try:
    if hasattr(st, "query_parameters"):
        if callable(st.query_parameters):
            params = st.query_parameters()
        else:
            params = st.query_parameters
    else:
        params = st.experimental_get_query_params()
except Exception:
    try:
        params = st.experimental_get_query_params()
    except Exception:
        params = {}

# Estraiamo il parametro 'match' gestendo sia il formato stringa che il formato lista
match_id = None
if "match" in params:
    valore = params["match"]
    if isinstance(valore, list) and len(valore) > 0:
        match_id = valore[0]
    else:
        match_id = valore

if match_id:
    try:
        percorso_file = os.path.join("match_data", f"{match_id}.json")
        
        if os.path.exists(percorso_file):
            with open(percorso_file, "r", encoding="utf-8") as f_in:
                pacchetto = json.load(f_in)
            
            info = pacchetto["info"]     # [campionato, data, arbitro, ass1, ass2]
            casa = pacchetto["casa"]     # [squadra, allenatore, giocatori_lista]
            ospite = pacchetto["ospite"] # [squadra, allenatore, giocatori_lista]
            
            # --- STILE GRAFICO ASD AZZURRA DUE CARRARE ---
            st.markdown("""
                <style>
                .main-title { color: #0096FF; text-align: center; font-size: 26px; font-weight: bold; margin-bottom: 2px; }
                .sub-title { color: #555; text-align: center; font-size: 15px; margin-bottom: 20px; line-height: 1.4; }
                .card-team { background-color: #E6F2FF; border-left: 5px solid #0096FF; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
                .team-name { color: #0096FF; font-size: 20px; font-weight: bold; margin: 0; }
                .all-name { color: #333; font-size: 14px; margin: 4px 0 0 0; }
                .player-row { display: flex; padding: 7px 0; border-bottom: 1px solid #E2E8F0; font-size: 15px; }
                .player-num { width: 35px; font-weight: bold; color: #0096FF; }
                .player-name { flex-grow: 1; color: #1A202C; }
                .player-year { width: 50px; color: #718096; text-align: right; }
                .info-footer { background-color: #F7FAFC; padding: 10px; border-radius: 4px; text-align: center; font-size: 13px; color: #4A5568; margin-top: 20px; }
                </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<p class="main-title">⚽ FORMAZIONI DI GARA LND</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="sub-title">🏆 <b>{info[0]}</b><br>📅 Data: {info[1]}</p>', unsafe_allow_html=True)
            
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa[0]}</p>'
                            f'<p class="all-name"><b>Allenatore:</b> {casa[1]}</p></div>', unsafe_allow_html=True)
                for g in casa[2]:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
            
            with col_m2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite[0]}</p>'
                            f'<p class="all-name"><b>Allenatore:</b> {ospite[1]}</p></div>', unsafe_allow_html=True)
                for g in ospite[2]:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="info-footer">🏁 <b>Arbitro:</b> {info[2]} | 🚩 <b>Assistenti:</b> {info[3]} - {info[4]}</div>', unsafe_allow_html=True)
            
            # WhatsApp Button per i dirigenti
            testo_condivisione = f"Formazioni {casa[0]} vs {ospite[0]} del {info[1]}: https://streamlit.app{match_id}"
            st.write("")
            st.page_link(f"https://whatsapp.com{testo_condivisione}", label="📲 Condividi Formazione su WhatsApp", icon="💬")
            
            st.stop() # INTERRUZIONE FORZATA: Mostra solo lo schermo azzurro mobile
        else:
            st.error("Inquadratura fallita: i dati di questa partita non sono memorizzati sul server.")
            st.stop()
    except Exception as e:
        st.error(f"Errore nel caricamento della distinta mobile: {e}")
        st.stop()

# ==============================================================================
# --- INTERFACCIA DI AMMINISTRAZIONE STANDARD (VISTA SOLO DA PC) ---
# ==============================================================================
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

    # --- GENERAZIONE PDF CON PAGINA WEB ESTERNA STATICA ---
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code", type="primary"):
        with st.spinner("Compilazione distinta e sincronizzazione pagina esterna..."):
            try:
                import json
                import base64
                import urllib.parse
                
                giocatori_casa_salvati = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
                giocatori_ospite_salvati = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
                
                squadra_casa_corretta = {"squadra": pulisci_testo(edit_nome_casa), "allenatore": pulisci_testo(edit_all_casa), "giocatori": giocatori_casa_salvati}
                squadra_ospite_corretta = {"squadra": pulisci_testo(edit_nome_ospite), "allenatore": pulisci_testo(edit_all_ospite), "giocatori": giocatori_ospite_salvati}
                info_gara_corrette = {"campionato": pulisci_testo(edit_campionato), "data": pulisci_testo(edit_data), "arbitro": pulisci_testo(edit_arbitro), "assistente1": pulisci_testo(edit_ass1), "assistente2": pulisci_testo(edit_ass2)}
                
                # Compattiamo solo i dati necessari togliendo le righe vuote
                casa_micro = [f"{g['N°']} - {g['GIOCATORE']} ({g['ANNO']})" for g in giocatori_casa_salvati if str(g["GIOCATORE"]).strip() != ""]
                ospite_micro = [f"{g['N°']} - {g['GIOCATORE']} ({g['ANNO']})" for g in giocatori_ospite_salvati if str(g["GIOCATORE"]).strip() != ""]
                
                dati_partita = {
                    "campionato": info_gara_corrette["campionato"], "data": info_gara_corrette["data"],
                    "arbitro": info_gara_corrette["arbitro"], "ass1": info_gara_corrette["assistente1"], "ass2": info_gara_corrette["assistente2"],
                    "squadra_casa": squadra_casa_corretta["squadra"], "all_casa": squadra_casa_corretta["allenatore"], "giocatori_casa": casa_micro,
                    "squadra_ospite": squadra_ospite_corretta["squadra"], "all_ospite": squadra_ospite_corretta["allenatore"], "giocatori_ospite": ospite_micro
                }
                
                # Convertiamo i dati in un formato compatto sicuro per il browser (Base64)
                json_string = json.dumps(dati_partita)
                base64_string = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
                url_encoded_data = urllib.parse.quote(base64_string)
                
                # --- IMPOSTA IL LINK DELLA TUA PAGINA GITHUB PAGES QUI ---
                # Modifica questa stringa se il tuo utente GitHub è diverso da 'duecarrare'
                link_pagina_esterna = "https://github.io"
                
                # Componiamo l'URL finale del QR Code
                pdf_url = f"{link_pagina_esterna.rstrip('/')}/?dati={url_encoded_data}"
                
                # Generazione fisica del QR Code
                qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=2)
                qr.add_data(pdf_url)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                buf_qr = io.BytesIO()
                img_qr.save(buf_qr, format="PNG")
                
                pdf_finale = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, buf_qr.getvalue())
                st.session_state["pdf_interattivo_pronto"] = pdf_finale
                st.session_state["ultimo_qr_link"] = pdf_url
                st.success("🎉 Distinta A4 generata e collegata alla pagina web esterna!")
            except Exception as ex:
                st.error(f"Errore di compilazione: {ex}")

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
