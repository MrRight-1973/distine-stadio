import streamlit as st
import json
import os

def render_pagina_spettatori():
    """Mostra la distinta live per i tifosi"""
    st.markdown("""
        <style>
        .main { background-color: #F0F4F8; }
        .titolo-match { text-align: center; color: #1A365D; font-size: 24px; font-weight: bold; margin-bottom: 5px; }
        .info-match { text-align: center; color: #4A5568; font-size: 14px; margin-bottom: 20px; }
        .card-squadra { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }
        .nome-squadra { color: #2B6CB0; font-size: 18px; font-weight: bold; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 10px; }
        .allenatore { font-style: italic; color: #4A5568; font-size: 13px; margin-bottom: 10px; }
        .riga-giocatore { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #EDF2F7; font-size: 15px; }
        .num-maglia { font-weight: bold; color: #2B6CB0; width: 25px; }
        .nome-giocatore { flex-grow: 1; text-align: left; padding-left: 5px; color: #2D3748; }
        .anno-giocatore { color: #A0AEC0; width: 40px; text-align: right; }
        .spazio-sicurezza-footer {
            height: 100px;
            margin-top: 20px;
            text-align: center;
            color: #A0AEC0;
            font-size: 12px;
            border-top: 1px dashed #CBD5E0;
            padding-top: 15px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='titolo-match'>⚽ AZZURRA DUE CARRARE</div>", unsafe_allow_html=True)
    st.markdown("<div class='titolo-match' style='font-size:18px; color:#2B6CB0;'>DISTINTA DIGITALE LIVE</div>", unsafe_allow_html=True)
    
    if not os.path.exists("distinta_corrente.json") or os.path.getsize("distinta_corrente.json") == 0:
        st.write("")
        st.warning("⌛ DISTINTA IN AGGIORNAMENTO\n\nLa segreteria sta caricando le distinte ufficiali della partita.")
        return
        
    try:
        with open("distinta_corrente.json", "r", encoding="utf-8") as f:
            dati = json.load(f)
            
        info = dati.get("info_gara", {})
        st.markdown(f"<div class='info-match'>🏆 {info.get('campionato', '')} | 📅 {info.get('data', '')}<br>🏁 Arbitro: {info.get('arbitro', '')}</div>", unsafe_allow_html=True)
        
        # Casa
        casa_dati = dati.get("casa", {})
        st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
        st.markdown(f"<div class='nome-squadra'>🏠 {casa_dati.get('squadra', 'SQUADRA CASA')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='allenatore'>All. {casa_dati.get('allenatore', '')}</div>", unsafe_allow_html=True)
        for g in casa_dati.get("giocatori", []):
            if g.get("GIOCATORE", "").strip():
                st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g.get('N°', '')}</span><span class='nome-giocatore'>{g.get('GIOCATORE', '')}</span><span class='anno-giocatore'>{g.get('ANNO', '')}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Ospite
        ospite_dati = dati.get("ospite", {})
        st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
        st.markdown(f"<div class='nome-squadra'>🚀 {ospite_dati.get('squadra', 'SQUADRA OSPITE')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='allenatore'>All. {ospite_dati.get('allenatore', '')}</div>", unsafe_allow_html=True)
        for g in ospite_dati.get("giocatori", []):
            if g.get("GIOCATORE", "").strip():
                st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g.get('N°', '')}</span><span class='nome-giocatore'>{g.get('GIOCATORE', '')}</span><span class='anno-giocatore'>{g.get('ANNO', '')}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='spazio-sicurezza-footer'>⚽ Azzurra Due Carrare Live</div>", unsafe_allow_html=True)
    except Exception:
        return
