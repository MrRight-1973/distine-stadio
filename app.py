import hmac
import io
import json
import os

import pandas as pd
import qrcode
import streamlit as st

from estrattore import analizza_distinta
from pdf_manager import genera_pdf
from squadra_manager import (
    giocatori_da_griglia,
    griglia_vuota,
    pulisci_widget_squadra,
    render_colonna_squadra,
    reset_stato_squadra,
)
from ui_components import render_download_buttons, render_info_match
from ui_spettatore import FILE_DISTINTA, FILE_PDF, render_pagina_spettatori

# Deve essere il PRIMO comando Streamlit
st.set_page_config(page_title="Distinta Digitale - Azzurra Due Carrare", page_icon="⚽", layout="wide")

LINK_PUBBLICO_DEFAULT = "https://distine-stadio.streamlit.app/"

# Menu, Deploy e barra superiore si nascondono da .streamlit/config.toml
st.markdown("<style>.block-container { padding-top: 1rem !important; }</style>", unsafe_allow_html=True)


def leggi_secret(nome, default=None):
    """Legge un secret senza esplodere se secrets.toml non esiste."""
    try:
        return st.secrets.get(nome, default)
    except Exception:
        return default


def rileva_mobile():
    try:
        user_agent = st.context.headers.get("User-Agent", "").lower()
    except Exception:  # Streamlit < 1.37
        return False
    return any(k in user_agent for k in ["android", "iphone", "ipad", "iemobile", "opera mini"])


def salva_distinta(pacchetto):
    """Scrittura atomica: i tifosi non leggono mai un file a metà."""
    tmp = FILE_DISTINTA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(pacchetto, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE_DISTINTA)


def salva_pdf_pubblico(pdf_bytes):
    """Salva il PDF sul server perché gli spettatori (altre sessioni) possano scaricarlo."""
    tmp = FILE_PDF + ".tmp"
    with open(tmp, "wb") as f:
        f.write(pdf_bytes)
    os.replace(tmp, FILE_PDF)


def genera_qr_png(link):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(link)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return buf.getvalue()


def firma_file(f):
    """Identifica il file per contenuto/id, non solo per nome (IMG_0001.jpg si ripete)."""
    if f is None:
        return ""
    return getattr(f, "file_id", None) or f"{f.name}-{f.size}"


def reset_solo_dati_ai():
    for chiave in ["dati_mappati", "macro_info", "firma_scansione_attiva", "pdf_interattivo_pronto"]:
        st.session_state.pop(chiave, None)
    reset_stato_squadra("griglia_casa")
    reset_stato_squadra("griglia_ospite")
    st.rerun()


def render_accesso_segreteria():
    st.markdown("---")
    with st.expander("⚙️ Area Riservata Segreteria"):
        password_corretta = leggi_secret("SEGRETERIA_PASSWORD")
        if not password_corretta:
            st.error("Password segreteria non configurata (SEGRETERIA_PASSWORD nei secrets).")
            return
        password_inserita = st.text_input("Inserisci la password di sblocco", type="password", key="pwd_segreteria")
        if st.button("Accedi al Pannello Gestionale", type="primary", use_container_width=True):
            if hmac.compare_digest(password_inserita.encode(), str(password_corretta).encode()):
                st.session_state["vista_attiva"] = "segreteria"
                st.rerun()
            else:
                st.error("❌ Password errata. Accesso negato.")


def render_segreteria():
    if st.button("⬅️ Torna alla Vista Spettatori (Mobile)", type="secondary"):
        st.session_state["vista_attiva"] = "pubblica"
        st.rerun()

    st.title("⚽ Centro Gestione Gara - Pannello PC Segreteria")
    st.write("La conferma delle liste aggiornerà la pagina web in tempo reale e genererà il PDF A4.")

    api_key_openai = leggi_secret("OPENAI_API_KEY")
    if not api_key_openai:
        st.warning("OPENAI_API_KEY non configurata nei secrets: la scansione AI non è disponibile.")

    if "griglia_casa" not in st.session_state:
        st.session_state["griglia_casa"] = griglia_vuota()
    if "griglia_ospite" not in st.session_state:
        st.session_state["griglia_ospite"] = griglia_vuota()

    col_f1, col_f2 = st.columns(2)
    file_casa = col_f1.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="uploader_file_casa")
    file_ospite = col_f2.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="uploader_file_ospite")

    c_scan, c_reset = st.columns(2)
    with c_reset:
        if st.button("🗑️ Svuota Liste e Ripristina Scansione", type="secondary", use_container_width=True):
            reset_solo_dati_ai()

    firma_correnti = f"{firma_file(file_casa)}__{firma_file(file_ospite)}"

    if file_casa and file_ospite:
        # File cambiati: la scansione precedente (e il PDF) non sono più validi
        if st.session_state.get("firma_scansione_attiva") != firma_correnti:
            st.session_state.pop("dati_mappati", None)
            st.session_state.pop("pdf_interattivo_pronto", None)

        if "dati_mappati" not in st.session_state:
            with c_scan:
                if st.button("🔍 Fase 1: Esegui Scansione AI delle Liste", type="primary", use_container_width=True):
                    with st.spinner("Estrazione giocatori e date in corso con GPT-4o..."):
                        try:
                            casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
                            ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                        except Exception as e:
                            st.error(f"Errore nell'estrazione: {e}")
                        else:
                            st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                            st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                            pulisci_widget_squadra("griglia_casa")
                            pulisci_widget_squadra("griglia_ospite")
                            st.session_state["macro_info"] = {
                                "campionato": casa_raw["campionato"], "data": casa_raw["data"],
                                "all_casa": casa_raw["allenatore"], "all_ospite": ospite_raw["allenatore"],
                            }
                            st.session_state["firma_scansione_attiva"] = firma_correnti
                            st.session_state["dati_mappati"] = True
                            st.rerun()

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
                dati_c = {**dati_c, "giocatori": giocatori_da_griglia("griglia_casa")}
                dati_o = {**dati_o, "giocatori": giocatori_da_griglia("griglia_ospite")}

                link_pubblico = leggi_secret("LINK_PUBBLICO", LINK_PUBBLICO_DEFAULT)
                pdf_bytes = genera_pdf(dati_c, dati_o, info_gara, genera_qr_png(link_pubblico))
                salva_pdf_pubblico(pdf_bytes)
                salva_distinta({"info_gara": info_gara, "casa": dati_c, "ospite": dati_o})
                st.session_state["pdf_interattivo_pronto"] = pdf_bytes
                st.success("🎉 Distinta online pubblicata sul link corretto! File PDF pronto.")

    render_download_buttons()


# --- ROUTING ---
is_mobile = rileva_mobile()

if "vista_attiva" not in st.session_state:
    st.session_state["vista_attiva"] = "pubblica"

if st.session_state["vista_attiva"] == "pubblica":
    render_pagina_spettatori()
    # L'area riservata si vede su PC, oppure da telefono aprendo il link con ?admin=1
    if not is_mobile or st.query_params.get("admin") == "1":
        render_accesso_segreteria()
else:
    render_segreteria()
