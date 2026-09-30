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

# BIVIO DI ACCESSO: Controlla se chi apre è lo spettatore dallo smartphone tramite QR Code
if st.query_params.get("view") == "public":
    render_pagina_spettatori()
else:
    # --- INTERFACCIA PC SEGRETERIA ---
    st.set_page_config(page_title="Pannello Segreteria - Azzurra Due Carrare", page_icon="⚽", layout="wide")
    st.title("⚽ Centro Gestione Gara - Pannello PC Segreteria")
    st.write("Carica i fogli gara. La conferma aggiornerà automaticamente la pagina web degli smartphone tifosi.")
    
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
        if st.button("⚡ Fase 3: Pubblica su Web e Genera PDF A4", type="primary", use_container_width=True):
            with st.spinner("Pubblicazione dati e scrittura PDF..."):
                dati_c["giocatori"] = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
                dati_o["giocatori"] = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
                
                # CONFIGURAZIONE STRUTTURATA: Forzatura del link esatto
                link_pubblico_spettatori = "https://streamlit.app"
                
                # Salva il file JSON condiviso sul server cloud
                pacchetto_gara = {"info_gara": info_gara, "casa": dati_c, "ospite": dati_o}
                with open("distinta_corrente.json", "w", encoding="utf-8") as f:
                    json.dump(pacchetto_gara, f, ensure_ascii=False, indent=2)
                
                # Generazione ottimizzata del QR Code (Risoluzione e contrasto migliorati per l'ottica mobile)
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=12,
                    border=4,
                )
                qr.add_data(link_pubblico_spettatori)
                qr.make(fit=True)
                
                buf_qr = io.BytesIO()
                qr.make_image(fill_color="black", back_color="white").save(buf_qr, format="PNG")
                
                st.session_state["pdf_interattivo_pronto"] = genera_pdf(dati_c, dati_o, info_gara, buf_qr.getvalue())
                st.success("🎉 Distinta online aggiornata con successo! Scarica il PDF e fai una prova di scansione.")

render_download_buttons()
