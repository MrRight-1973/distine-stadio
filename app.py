import streamlit as st
import qrcode
import io
import json
import pandas as pd
from estrattore import analizza_distinta
from pdf_manager import genera_pdf
from squadra_manager import render_colonna_squadra
from ui_components import render_info_match, render_download_buttons
from ui_spettatore import render_pagina_spettatori

# DISATTIVAZIONE INTERAZIONE LOGHI ESTERNI (PC + MOBILE)
st.markdown("""
    <style>
    /* Rimuove e nasconde il footer "Made with Streamlit", i badge e i menu nativi */
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stFooter"] {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    
    /* Annulla qualsiasi click residuo o tocco del dito */
    .viewerBadge_container__1QS13, 
    a[href*="streamlit.io"], 
    a[href*="github.com"] {
        pointer-events: none !important;   
        opacity: 0 !important;             
        background: transparent !important;
    }
    
    /* Ottimizzazione dei margini superiori */
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Estrazione sicura dello User-Agent per identificare i telefoni ed evitare errori sul server
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(OS_mobile in user_agent for OS_mobile in ["android", "iphone", "ipad", "iemobile", "opera mini"])

# Gestione solida della vista tramite Session State
if "vista_attiva" not in st.session_state:
    st.session_state["vista_attiva"] = "pubblica"

# Se l'utente è un tifoso (o lo stato è su pubblica), mostra solo il Match Program digitale
if st.session_state["vista_attiva"] == "pubblica":
    render_pagina_spettatori()
    
    # Il pulsante di sblocco appare ESCLUSIVAMENTE sui PC fissi, mai sugli smartphone
    if not is_mobile:
        st.markdown("---")
        with st.expander("⚙️ Area Riservata Segreteria PC"):
            password_inserita = st.text_input("Inserisci la password di sblocco", type="password", key="pwd_segreteria")
            if st.button("Accedi al Pannello Gestionale", type="primary", use_container_width=True):
                # PASSWORD UFFICIALE DI ACCESSO
                if password_inserita == "azzurra2026":
                    st.session_state["vista_attiva"] = "segreteria"
                    st.rerun()
                else:
                    st.error("❌ Password errata. Accesso negato.")
else:
    # --- INTERFACCIA PC SEGRETERIA GESTIONALE ---
    st.set_page_config(page_title="Pannello Segreteria - Azzurra Due Carrare", page_icon="⚽", layout="wide")
    
    if st.button("⬅️ Torna alla Vista Spettatori (Mobile)", type="secondary"):
        st.session_state["vista_attiva"] = "pubblica"
        st.rerun()
        
    st.title("⚽ Centro Gestione Gara - Pannello PC Segreteria")
    st.write("La conferma delle liste aggiornerà la pagina web in tempo reale e genererà il PDF A4.")
    
    api_key_openai = st.secrets.get("OPENAI_API_KEY")

    def reset_solo_dati_ai():
        chiavi_da_eliminare = ["dati_mappati", "macro_info", "firma_scansione_attiva", "pdf_interattivo_pronto"]
        for chiave in chiavi_da_eliminare:
            if chiave in st.session_state:
                del st.session_state[chiave]
        st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
        st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
        st.rerun()

    if "griglia_casa" not in st.session_state:
        st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
    if "griglia_ospite" not in st.session_state:
        st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")

    col_f1, col_f2 = st.columns(2)
    file_casa = col_f1.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="uploader_file_casa")
    file_ospite = col_f2.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="uploader_file_ospite")

    c_scan, c_reset = st.columns(2)
    with c_reset:
        if st.button("🗑️ Svuota Liste e Ripristina Scansione", type="secondary", use_container_width=True):
            reset_solo_dati_ai()

    firma_file_correnti = f"{file_casa.name if file_casa else ''}__{file_ospite.name if file_ospite else ''}"

    if file_casa and file_ospite:
        if st.session_state.get("firma_scansione_attiva") != firma_file_correnti:
            if "dati_mappati" in st.session_state:
                del st.session_state["dati_mappati"]

        if "dati_mappati" not in st.session_state:
            with c_scan:
                if st.button("🔍 Fase 1: Esegui Scansione AI delle Liste", type="primary", use_container_width=True):
                    with st.spinner("Estrazione giocatori e date in corso con GPT-4o..."):
                        try:
                            casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
                            ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                            st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                            st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                            st.session_state["macro_info"] = {
                                "campionato": casa_raw["campionato"], "data": casa_raw["data"], 
                                "all_casa": casa_raw["allenatore"], "all_ospite": ospite_raw["allenatore"]
                            }
                            st.session_state["firma_scansione_attiva"] = firma_file_correnti
                            st.session_state["dati_mappati"] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore nell'estrazione: {e}")

    if "dati_mappati" in st.session_state:
        st.markdown("---")
        info_gara = render_info_match(st.session_state["macro_info"])
        
        st.markdown("---")
        c_sq1, c_sq2 = st.columns(2)
        inf = st.session_state["macro_info"]
        
        with c_sq1:
            dati_c = render_colonna_squadra("🏠 SQUADRA CASA", "griglia_casa", inf["all_casa"])
        with c_sq2:
            dati_o = render_colonna_squadra("🚀 SQUADRA OSPITE", "griglia_ospite", inf["all_ospite"])

        st.markdown("---")
# --- Dentro app.py, sotto il bottone Fase 3 ---
if st.button("⚡ Fase 3: Pubblica su Web e Genera PDF A4", type="primary", use_container_width=True):
    with st.spinner("Pubblicazione dati e scrittura PDF..."):
        dati_c["giocatori"] = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
        dati_o["giocatori"] = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
        
        link_pubblico_spettatori = "https://streamlit.app"
        
        # Generiamo il PDF
        pdf_bytes = genera_pdf(dati_c, dati_o, info_gara, None) # Rimosso QR code se non serve più nel PDF, o lascialo se vuoi
        st.session_state["pdf_interattivo_pronto"] = pdf_bytes
        
        # SALVATAGGIO FISICO DEL PDF SUL SERVER PER I TIFOSI
        with open("distinta_ultimo_match.pdf", "wb") as f:
            f.write(pdf_bytes)
            
        st.success("🎉 Distinta pubblicata con successo! I tifosi ora possono scaricare il PDF.")
