import streamlit as st
import io
import qrcode
import requests
import base64
import pandas as pd
from estrattore import analizza_distinta, genera_pdf, pulisci_testo

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara Gestionale")
st.write("Carica i fogli gara ed effettua modifiche o slittamenti istantanei sulle liste.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

# Inizializzazione Session State
if "griglia_casa" not in st.session_state:
    st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
if "griglia_ospite" not in st.session_state:
    st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
if "macro_info" not in st.session_state:
    st.session_state["macro_info"] = {}
if "elaborato" not in st.session_state:
    st.session_state["elaborato"] = False

# Layout Caricamento File
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
with col_f2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")

# Fase 1: Scansione AI
if file_casa and file_ospite:
    if st.button("🔍 Fase 1: Esegui Scansione AI delle Immagini", type="primary"):
        with st.spinner("L'AI sta leggendo le distinte..."):
            try:
                casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
                ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                
                # Conversione in DataFrame (assumendo che l'AI restituisca il campo "N°")
                st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                
                # Salvataggio Macro Info (Completato il dizionario interrotto)
                st.session_state["macro_info"] = {
                    "campionato": casa_raw.get("campionato", ""),
                    "data": casa_raw.get("data", ""),
                    "squadra_casa": casa_raw.get("squadra", "Casa"),
                    "all_casa": casa_raw.get("allenatore", ""),
                    "squadra_ospite": ospite_raw.get("squadra", "Ospite"),
                    "all_ospite": ospite_raw.get("allenatore", "")
                }
                st.session_state["elaborato"] = True
                st.success("Scansione completata con successo!")
            except Exception as e:
                st.error(f"Errore durante l'analisi delle distinte: {e}")

# Fase 2: Visualizzazione e Modifica (Attiva solo se l'elaborazione è avvenuta)
if st.session_state["elaborato"]:
    st.divider()
    st.subheader("📝 Fase 2: Modifica e Verifica i Dati")
    
    # Mostra Info Generali del Match
    info = st.session_state["macro_info"]
    st.info(f"**Competizione:** {info['campionato']} | **Data:** {info['data']}")
    
    col_ed1, col_ed2 = st.columns(2)
    with col_ed1:
        st.write(f"### {info['squadra_casa']} (Allenatore: {info['all_casa']})")
        # Salviamo l'output modificato dall'utente
        griglia_casa_modificata = st.data_editor(st.session_state["griglia_casa"], num_rows="dynamic", key="editor_casa")
    
    with col_ed2:
        st.write(f"### {info['squadra_ospite']} (Allenatore: {info['all_ospite']})")
        # Salviamo l'output modificato dall'utente
        griglia_ospite_modificata = st.data_editor(st.session_state["griglia_ospite"], num_rows="dynamic", key="editor_ospite")

    st.divider()
    st.subheader("🖨️ Fase 3: Esportazione")

    try:
        # 1. Richiamiamo la tua funzione custom per generare il PDF passando i dati aggiornati
        # Nota: adegua i parametri in base a come è definita esattamente la tua 'genera_pdf' in estrattore.py
        pdf_bytes = genera_pdf(
            info=info, 
            df_casa=griglia_casa_modificata, 
            df_ospite=griglia_ospite_modificata
        )
        
        # 2. Creiamo il pulsante nativo di Streamlit per scaricare il file
        st.download_button(
            label="📄 Scarica PDF Distinta Unificata",
            data=pdf_bytes,
            file_name=f"distinta_{info['squadra_casa']}_vs_{info['squadra_ospite']}.pdf",
            mime="application/pdf",
            type="primary"
        )
        
    except Exception as e:
        st.error(f"Errore durante la creazione del PDF: {e}")
