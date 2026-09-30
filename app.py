import streamlit as st
import qrcode
import io
import json
import os
import pandas as pd
import base64
from estrattore import analizza_distinta
from pdf_manager import genera_pdf
from squadra_manager import render_colonna_squadra
from ui_components import render_info_match, render_download_buttons
from ui_spettatore import render_pagina_spettatori

# 1. IMPOSTAZIONE CONFIGURAZIONE PAGINA (Deve essere la prima istruzione)
st.set_page_config(page_title="Azzurra Due Carrare - Distinte", page_icon="⚽", layout="wide")

# --- INTERCETTAZIONE E OTTIMIZZAZIONE DOWNLOAD DA QR CODE ---
if st.query_params.get("download") == "true":
    if os.path.exists("distinta_corrente.pdf") and os.path.getsize("distinta_corrente.pdf") > 0:
        f_read_pdf = open("distinta_corrente.pdf", "rb")
        pdf_bytes = f_read_pdf.read()
        f_read_pdf.close()
        
        # Trasforma il PDF in stringa leggibile dal browser mobile
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Interfaccia pulita a tutto schermo ottimizzata per smartphone
        st.markdown(f"""
            <style>
            .stApp {{ background-color: #F0F4F8; }}
            .box-download {{
                text-align: center;
                margin-top: 15vh;
                padding: 30px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }}
            .bottone-click {{
                display: block;
                width: 100%;
                background-color: #2B6CB0;
                color: white !important;
                text-decoration: none !important;
                padding: 18px;
                font-size: 20px;
                font-weight: bold;
                border-radius: 10px;
                margin-top: 25px;
                box-shadow: 0 4px 12px rgba(43, 108, 176, 0.4);
            }}
            </style>
            <div class='box-download'>
                <h2 style='color: #1A365D;'>⚽ AZZURRA DUE CARRARE</h2>
                <p style='color: #4A5568; font-size: 16px;'>La distinta ufficiale di gara in formato PDF A4 è pronta.</p>
                <a href="data:application/pdf;base64,{b64_pdf}" download="distinta_ufficiale_gara.pdf" class="bottone-click">
                    📥 PREMI QUI PER SCARICARE IL PDF
                </a>
                <p style='color: #A0AEC0; font-size: 12px; margin-top: 20px;'>Il file verrà salvato nella cartella Download del tuo smartphone.</p>
            </div>
        """, unsafe_allow_html=True)
        st.stop() # Blocca categoricamente l'esecuzione del resto dell'app
    else:
        st.warning("⌛ DISTINTA IN AGGIORNAMENTO - Il file PDF non è ancora pronto sul server. Riprova tra qualche istante.")
        st.stop()

# 2. DISATTIVAZIONE INTERAZIONE LOGHI ESTERNI (PC + MOBILE)
st.markdown("""
    <style>
    .viewerBadge_container__1QS13, 
    div[class*="viewerBadge"], 
    a[href*="streamlit.io"], 
    a[href*="github.com"],
    footer, 
    div[data-testid="stFooter"],
    header,
    .stAppDeployButton {
        pointer-events: none !important;
        opacity: 0 !important;
        background: transparent !important;
    }
    .block-container { padding-top: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# Controllo se l'utente usa uno smartphone
user_agent = st.context.headers.get("User-Agent", "").lower()
is_mobile = any(OS_mobile in user_agent for OS_mobile in ["android", "iphone", "ipad", "iemobile", "opera mini"])

if "vista_attiva" not in st.session_state:
    st.session_state["vista_attiva"] = "pubblica"

# Mostra la vista pubblica standard per chi naviga l'URL classico senza parametri
if st.session_state["vista_attiva"] == "pubblica":
    render_pagina_spettatori()
    
    if not is_mobile:
        st.markdown("---")
        with st.expander("⚙️ Area Riservata Segreteria PC"):
            password_inserita = st.text_input("Inserisci la password di sblocco", type="password", key="pwd_segreteria")
            if st.button("Accedi al Pannello Gestionale", type="primary", use_container_width=True):
                if password_inserita == "azzurra2026":
                    st.session_state["vista_attiva"] = "segreteria"
                    st.rerun()
                else:
                    st.error("❌ Password errata. Accesso negato.")
else:
    # --- INTERFACCIA PC SEGRETERIA GESTIONALE ---
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
        if os.path.exists("distinta_corrente.pdf"):
            os.remove("distinta_corrente.pdf")
        if os.path.exists("distinta_corrente.json"):
            os.remove("distinta_corrente.json")
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
        if st.button("⚡ Fase 3: Pubblica su Web e Genera PDF A4", type="primary", use_container_width=True):
            with st.spinner("Pubblicazione dati e scrittura PDF..."):
                dati_c["giocatori"] = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
                dati_o["giocatori"] = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
                
                link_download_diretto = "https://streamlit.app"
                
                pacchetto_gara = {"info_gara": info_gara, "casa": dati_c, "ospite": dati_o}
                f_json = open("distinta_corrente.json", "w", encoding="utf-8")
                json.dump(pacchetto_gara, f_json, ensure_ascii=False, indent=2)
                f_json.close()
                
                qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
                qr.add_data(f"{link_download_diretto}?download=true")
                qr.make(fit=True)
                
                buf_qr = io.BytesIO()
                qr.make_image(fill_color="black", back_color="white").save(buf_qr, format="PNG")
                
                pdf_bytes = genera_pdf(dati_c, dati_o, info_gara, buf_qr.getvalue())
                
# --- SCRITTURA PDF SENZA BLOCCO WITH PER EVITARE AL 100% ERRORI DI INDENTAZIONE ---
f_write_pdf = open("distinta_corrente.pdf", "wb")
f_write_pdf.write(pdf_bytes)
f_write_pdf.close()
st.session_state["pdf_interattivo_pronto"] = pdf_bytes
st.success("🎉 Distinta pubblicata! Il QR code ora scarica direttamente il PDF A4.")
render_download_buttons()
