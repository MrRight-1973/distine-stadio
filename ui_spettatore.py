import streamlit as st
import json
import os

def render_pagina_spettatori():
    """Mostra la distinta in tempo reale ottimizzata per gli smartphone dei tifosi"""
st.markdown("""
    <style>
    /* 1. ABBATTIMENTO DEI CONTENITORI SPECIFICI DI STREAMLIT CLOUD */
    [data-testid="stStatusWidget"],
    [data-testid="stFooter"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    div[class*="viewerBadge"],
    div[class*="StatusWidget"],
    div[class*="StyledEmbedControlBar"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        max-height: 0px !important;
        width: 0px !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }

    /* 2. ELIMINAZIONE DEL CUSCINETTO DI SPAZIO CHE IL TELEFONO CREA PER IL BADGE */
    iframe {
        display: none !important;
    }
    .stApp {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    </style>
""", unsafe_allow_html=True)
    
    st.markdown("<div class='titolo-match'>⚽ AZZURRA DUE CARRARE</div>", unsafe_allow_html=True)
    st.markdown("<div class='titolo-match' style='font-size:18px; color:#2B6CB0;'>DISTINTA DIGITALE LIVE</div>", unsafe_allow_html=True)
    
    if not os.path.exists("distinta_corrente.json") or os.path.getsize("distinta_corrente.json") == 0:
        st.write("")
        st.warning("⌛ DISTINTA IN AGGIORNAMENTO\n\nLa segreteria sta caricando le distinte ufficiali della partita. Riprova tra qualche istante o rinfresca la pagina.")
        return
        
    try:
        with open("distinta_corrente.json", "r", encoding="utf-8") as f:
            dati = json.load(f)
            
        info = dati.get("info_gara", {})
        campionato = info.get("campionato", "")
        data_gara = info.get("data", "")
        arbitro = info.get("arbitro", "")
        
        st.markdown(f"<div class='info-match'>🏆 {campionato} | 📅 {data_gara}<br>🏁 Arbitro: {arbitro}</div>", unsafe_allow_html=True)
        
        # Render Squadra Casa
        casa_dati = dati.get("casa", {})
        st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
        st.markdown(f"<div class='nome-squadra'>🏠 {casa_dati.get('squadra', 'SQUADRA CASA')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='allenatore'>All. {casa_dati.get('allenatore', '')}</div>", unsafe_allow_html=True)
        
        for g in casa_dati.get("giocatori", []):
            nome_g = g.get("GIOCATORE", "")
            if nome_g.strip():
                st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g.get('N°', '')}</span><span class='nome-giocatore'>{nome_g}</span><span class='anno-giocatore'>{g.get('ANNO', '')}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Render Squadra Ospite
        ospite_dati = dati.get("ospite", {})
        st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
        st.markdown(f"<div class='nome-squadra'>🚀 {ospite_dati.get('squadra', 'SQUADRA OSPITE')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='allenatore'>All. {ospite_dati.get('allenatore', '')}</div>", unsafe_allow_html=True)
        
        for g in ospite_dati.get("giocatori", []):
            nome_g = g.get("GIOCATORE", "")
            if nome_g.strip():
                st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g.get('N°', '')}</span><span class='nome-giocatore'>{nome_g}</span><span class='anno-giocatore'>{g.get('ANNO', '')}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception:
        st.warning("⌛ Aggiornamento liste in corso da parte della segreteria...")
        return
        
