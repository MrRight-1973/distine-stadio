import streamlit as st
import qrcode
import io
import pandas as pd
from estrattore import analizza_distinta
from pdf_manager import genera_pdf
from squadra_manager import render_colonna_squadra
from ui_components import render_info_match, render_download_buttons

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")
st.title("⚽ Centro Gestione Distinte Gara")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

# Funzione di reset mirata: cancella le tabelle e i dati AI, ma NON i file caricati
def reset_solo_dati_ai():
    chiavi_da_eliminare = ["dati_mappati", "macro_info", "firma_scansione_attiva", "pdf_interattivo_pronto"]
    for chiave in chiavi_da_eliminare:
        if chiave in st.session_state:
            del st.session_state[chiave]
    
    # Ripristina le griglie vuote
    st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
    st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
    st.rerun()

# Inizializzazione standard griglie
if "griglia_casa" not in st.session_state:
    st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
if "griglia_ospite" not in st.session_state:
    st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")

# Area di Caricamento File fisici
col_f1, col_f2 = st.columns(2)
file_casa = col_f1.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="uploader_file_casa")
file_ospite = col_f2.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="uploader_file_ospite")

# I due pulsanti principali posizionati in modo stabile sotto l'uploader
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
    if st.button("⚡ Fase 3: Conferma e Genera PDF", type="primary", use_container_width=True):
        with st.spinner("Generazione del file..."):
            dati_c["giocatori"] = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
            dati_o["giocatori"] = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
            
            qr = qrcode.QRCode(version=1, border=1)
            qr.add_data("https://streamlit.app")
            buf_qr = io.BytesIO()
            qr.make_image().save(buf_qr, format="PNG")
            
            st.session_state["pdf_interattivo_pronto"] = genera_pdf(dati_c, dati_o, info_gara, buf_qr.getvalue())
            st.success("🎉 Documento A4 pronto!")

render_download_buttons()
