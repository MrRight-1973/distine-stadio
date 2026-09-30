import streamlit as st
import io
import qrcode
import pandas as pd

# Import moduli spezzettati
from utils import pulisci_testo
from ai_extractor import analizza_distinta
from pdf_generator import genera_pdf

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara Gestionale")
st.write("Carica i fogli gara ed effettua modifiche o slittamenti istantanei sulle liste.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

# Inizializzazione Tabelle Vuote
if "griglia_casa" not in st.session_state:
    st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
if "griglia_ospite" not in st.session_state:
    st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")

# FASE 1: Caricamento File
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
with col_f2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")

if file_casa and file_ospite and "dati_mappati" not in st.session_state:
    if st.button("🔍 Fase 1: Esegui Scansione AI delle Immagini", type="primary"):
        with st.spinner("L'AI sta analizzando i documenti in parallelo..."):
            try:
                # Esecuzione mirata passando esplicitamente i ruoli separati all'estrattore
                casa_raw = analizza_distinta(file_casa, "LOCALE / CASA", api_key_openai)
                ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                
                # Popolamento isolato delle griglie
                st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                
                # Salvataggio separato e accurato delle macro informazioni
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
                st.error(f"Errore durante l'analisi visiva programmata: {e}")

# FASE 2: Modifica e Funzioni di Shift (Slittamento)
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
    opzioni_righe = list(range(1, 21))
    
    # --- Gestione Squadra Casa ---
    with c_sq1:
        st.subheader("🏠 SQUADRA CASA")
        edit_nome_casa = st.text_input("Nome Società Ospitante", value=info["squadra_casa"])
        edit_all_casa = st.text_input("Allenatore Ospitante", value=info["all_casa"])
        st.session_state["griglia_casa"] = st.data_editor(st.session_state["griglia_casa"], key="editor_casa_current", use_container_width=True)
        
        c_ctrl_c1, c_ctrl_c2 = st.columns([1, 1])
        with c_ctrl_c1:
            riga_scelta_casa = st.selectbox("🎯 Riga (Casa)", options=opzioni_righe, index=12, key="sel_casa")
        with c_ctrl_c2:
            st.write("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("⬇️", key="shift_down_casa", use_container_width=True):
                    df = st.session_state["griglia_casa"].copy().reset_index()
                    idx = riga_scelta_casa - 1
                    df_nuovo = pd.concat([df.iloc[:idx], pd.DataFrame([{"N°": riga_scelta_casa, "GIOCATORE": "", "ANNO": ""}]), df.iloc[idx:19]]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_casa"] = df_nuovo.set_index("N°")
                    st.rerun()
            with c_btn2:
                if st.button("⬆️", key="shift_up_casa", use_container_width=True):
                    df = st.session_state["griglia_casa"].copy().reset_index()
                    idx = riga_scelta_casa - 1
                    df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_casa"] = df_nuovo.set_index("N°")
                    st.rerun()

    # --- Gestione Squadra Ospite ---
    with c_sq2:
        st.subheader("🚀 SQUADRA OSPITE")
        edit_nome_ospite = st.text_input("Nome Società Ospite", value=info["squadra_ospite"])
        edit_all_ospite = st.text_input("Allenatore Ospite", value=info["all_ospite"])
        st.session_state["griglia_ospite"] = st.data_editor(st.session_state["griglia_ospite"], key="editor_ospite_current", use_container_width=True)
        
        c_ctrl_o1, c_ctrl_o2 = st.columns([1, 1])
        with c_ctrl_o1:
            riga_scelta_ospite = st.selectbox("🎯 Riga (Ospite)", options=opzioni_righe, index=12, key="sel_ospite")
        with c_ctrl_o2:
            st.write("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
            o_btn1, o_btn2 = st.columns(2)
            with o_btn1:
                if st.button("⬇️", key="shift_down_ospite", use_container_width=True):
                    df = st.session_state["griglia_ospite"].copy().reset_index()
                    idx = riga_scelta_ospite - 1
                    df_nuovo = pd.concat([df.iloc[:idx], pd.DataFrame([{"N°": riga_scelta_ospite, "GIOCATORE": "", "ANNO": ""}]), df.iloc[idx:19]]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_ospite"] = df_nuovo.set_index("N°")
                    st.rerun()
            with o_btn2:
                if st.button("⬆️", key="shift_up_ospite", use_container_width=True):
                    df = st.session_state["griglia_ospite"].copy().reset_index()
                    idx = riga_scelta_ospite - 1
                    df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_ospite"] = df_nuovo.set_index("N°")
                    st.rerun()

    # FASE 3: Generazione Esito PDF
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code", type="primary"):
        with st.spinner("Generazione del foglio di gara A4 definitivo..."):
            try:
                casa_data = {
                    "squadra": pulisci_testo(edit_nome_casa), "allenatore": pulisci_testo(edit_all_casa),
                    "giocatori": st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
                }
                ospite_data = {
                    "squadra": pulisci_testo(edit_nome_ospite), "allenatore": pulisci_testo(edit_all_ospite),
                    "giocatori": st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
                }
                info_gara = {
                    "campionato": pulisci_testo(edit_campionato), "data": pulisci_testo(edit_data),
                    "arbitro": pulisci_testo(edit_arbitro), "assistente1": pulisci_testo(edit_ass1), "assistente2": pulisci_testo(edit_ass2)
                }
                
                # Generazione QR Code
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data("https://streamlit.app")
                qr.make(fit=True)
                buf_qr = io.BytesIO()
                qr.make_image(fill_color="black", back_color="white").save(buf_qr, format="PNG")
                
                st.session_state["pdf_ready"] = genera_pdf(casa_data, ospite_data, info_gara, buf_qr.getvalue())
                st.success("🎉 Documento A4 unificato generato con successo!")
            except Exception as ex:
                st.error(f"Si è verificato un errore durante la compilazione finale: {ex}")

if "pdf_ready" in st.session_state:
    st.write("")
    c_dl1, c_dl2 = st.columns(2)
    with c_dl1:
        st.download_button("💾 Scarica PDF per il Computer", data=st.session_state["pdf_ready"], file_name="distinta_A4.pdf", mime="application/pdf", use_container_width=True)
    with c_dl2:
        st.download_button("📥 Scarica PDF su Smartphone", data=st.session_state["pdf_ready"], file_name="distinta_A4_mobile.pdf", mime="application/pdf", type="primary", use_container_width=True)
