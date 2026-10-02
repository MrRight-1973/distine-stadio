import html
import json
import logging
import os

import streamlit as st

log = logging.getLogger(__name__)

# Percorso assoluto: indipendente dalla cartella di lavoro
FILE_DISTINTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "distinta_corrente.json")
FILE_PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "distinta_corrente.pdf")

CSS = """
<style>
.stApp { background-color: #F0F4F8; }
.block-container { max-width: 700px; margin: 0 auto; }
.titolo-match { text-align: center; color: #1A365D; font-size: 24px; font-weight: bold; margin-bottom: 5px; }
.info-match { text-align: center; color: #4A5568; font-size: 14px; margin-bottom: 20px; }
.card-squadra { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
.nome-squadra { color: #2B6CB0; font-size: 18px; font-weight: bold; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 10px; }
.allenatore { font-style: italic; color: #4A5568; font-size: 13px; margin-bottom: 10px; }
.riga-giocatore { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #EDF2F7; font-size: 15px; }
.num-maglia { font-weight: bold; color: #2B6CB0; width: 25px; }
.nome-giocatore { flex-grow: 1; text-align: left; padding-left: 5px; color: #2D3748; }
.anno-giocatore { color: #A0AEC0; width: 40px; text-align: right; }
/* Cuscinetto protettivo: isola i loghi Streamlit in un'area vuota */
.spazio-sicurezza-footer { height: 120px; margin-top: 20px; text-align: center; color: #A0AEC0; font-size: 12px; border-top: 1px dashed #CBD5E0; padding-top: 15px; }
</style>
"""


def _t(valore):
    """Testo sicuro per l'HTML (None -> stringa vuota)."""
    return "" if valore is None else html.escape(str(valore))


def _html_card(icona, dati, titolo_default):
    """Costruisce l'intera card in UNA stringa: Streamlit isola ogni st.markdown,
    quindi div aperti/chiusi in chiamate separate non avvolgono il contenuto."""
    parti = [
        "<div class='card-squadra'>",
        f"<div class='nome-squadra'>{icona} {_t(dati.get('squadra') or titolo_default)}</div>",
    ]
    if dati.get("allenatore"):
        parti.append(f"<div class='allenatore'>All. {_t(dati.get('allenatore'))}</div>")

    for g in dati.get("giocatori") or []:
        nome = (g.get("GIOCATORE") or "").strip()
        if nome:
            parti.append(
                "<div class='riga-giocatore'>"
                f"<span class='num-maglia'>{_t(g.get('N°'))}</span>"
                f"<span class='nome-giocatore'>{_t(nome)}</span>"
                f"<span class='anno-giocatore'>{_t(g.get('ANNO'))}</span>"
                "</div>"
            )
    parti.append("</div>")
    return "".join(parti)


@st.fragment(run_every="30s")
def _contenuto_distinta():
    """Rilegge la distinta ogni 30 secondi senza ricaricare la pagina."""
    if not os.path.exists(FILE_DISTINTA) or os.path.getsize(FILE_DISTINTA) == 0:
        st.warning("⌛ DISTINTA IN AGGIORNAMENTO\n\nLa segreteria sta caricando le distinte ufficiali della partita. La pagina si aggiorna da sola.")
        return

    try:
        with open(FILE_DISTINTA, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except (json.JSONDecodeError, OSError):
        st.warning("⌛ Aggiornamento liste in corso da parte della segreteria...")
        return

    try:
        info = dati.get("info_gara", {})
        st.markdown(
            f"<div class='info-match'>🏆 {_t(info.get('campionato'))} | 📅 {_t(info.get('data'))}"
            f"<br>🏁 Arbitro: {_t(info.get('arbitro'))}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(_html_card("🏠", dati.get("casa", {}), "SQUADRA CASA"), unsafe_allow_html=True)
        st.markdown(_html_card("🚀", dati.get("ospite", {}), "SQUADRA OSPITE"), unsafe_allow_html=True)
        st.markdown(
            "<div class='spazio-sicurezza-footer'>Aggiornamento automatico ogni 30 secondi</div>",
            unsafe_allow_html=True,
        )
    except Exception:
        log.exception("Errore nel rendering della distinta spettatori")
        st.warning("⌛ Aggiornamento liste in corso da parte della segreteria...")


def _render_pulsante_pdf():
    """Pulsante grande in cima: chi inquadra il QR scarica il PDF con un solo tocco."""
    if not os.path.exists(FILE_PDF):
        return
    try:
        with open(FILE_PDF, "rb") as f:
            dati_pdf = f.read()
    except OSError:
        return
    st.download_button(
        label="📄 SCARICA LA DISTINTA (PDF)",
        data=dati_pdf,
        file_name="distinta_ufficiale_A4.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
        key="dl_pdf_spettatori",
    )


def render_pagina_spettatori():
    """Mostra la distinta in tempo reale ottimizzata per gli smartphone dei tifosi"""
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<div class='titolo-match'>⚽ AZZURRA DUE CARRARE</div>", unsafe_allow_html=True)
    st.markdown("<div class='titolo-match' style='font-size:18px; color:#2B6CB0;'>DISTINTA DIGITALE LIVE</div>", unsafe_allow_html=True)
    _render_pulsante_pdf()
    _contenuto_distinta()
