import streamlit as st
import qrcode
import io
import pandas as pd
from estrattore import analizza_distinta, pulisci_testo
from pdf_manager import genera_pdf
from squadra_manager import render_colonna_squadra
from ui_components import render_info_match, render_download_buttons

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")
st.title("⚽ Centro Gestione Distinte Gara Gestionale")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

# Inizializzazione Session State
for chiave in ["griglia_casa", "griglia_ospite"]:
    if chiave not in st.session_state:
        st.session_state[chiave] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")

# Upload File Iniciale
col_f1, col_f2 = st.columns(2)
file_casa = col_f1.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
file_ospite = col_f2.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")

if file_casa and file_ospite and "dati_mappati" not in st.session_state:
    if st.button("🔍 Fase 1: Esegui Scansione AI delle Immagini", type="primary"):
        with st.spinner("Estrazione dati, capitani e assistenti in corso..."):
            casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
            ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
            
            st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
            st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
            st.session_state["macro_info"] = {
                "campionato": casa_raw["campionato"], "data": casa_raw["data"], 
                "squadra_casa": casa_raw["squadra"], "all_casa": casa_raw["allenatore"], "guardalinee_casa": casa_raw["guardalinee_parte"],
                "squadra_ospite": ospite_raw["squadra"], "all_ospite": ospite_raw["allenatore"], "guardalinee_ospite": ospite_raw["guardalinee_parte"]
            }
            st.session_state["dati_mappati"] = True
            st.rerun()

if "dati_mappati" in st.session_state:
    st.markdown("---")
    info_gara = render_info_match(st.session_state["macro_info"])
    
    st.markdown("---")
    c_sq1, c_sq2 = st.columns(2)
    inf = st.session_state["macro_info"]
    
    with c_sq1:
        dati_c = render_colonna_squadra("🏠 SQUADRA CASA", "griglia_casa", inf["squadra_casa"], inf["all_casa"], inf["guardalinee_casa"])
    with c_sq2:
        dati_o = render_colonna_squadra("🚀 SQUADRA OSPITE", "griglia_ospite", inf["squadra_ospite"], inf["all_ospite"], inf["guardalinee_ospite"])

    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code", type="primary"):
        with st.spinner("Generazione del foglio di gara..."):
            dati_c["giocatori"] = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
            dati_o["giocatori"] = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
            
            # Generazione QR Code rapida
            qr = qrcode.QRCode(version=1, border=1)
            qr.add_data("https://streamlit.app")
            buf_qr = io.BytesIO()
            qr.make_image().save(buf_qr, format="PNG")
            
            st.session_state["pdf_interattivo_pronto"] = genera_pdf(dati_c, dati_o, info_gara, buf_qr.getvalue())
            st.success("🎉 Documento A4 unificato pronto!")

render_download_buttons()
