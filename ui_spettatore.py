import streamlit as st
import json
import os

def render_pagina_spettatori():
    """Mostra la distinta in tempo reale ottimizzata per gli smartphone dei tifosi"""
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
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='titolo-match'>⚽ AZZURRA DUE CARRARE</div>", unsafe_allow_html=True)
    st.markdown("<div class='titolo-match' style='font-size:18px; color:#2B6CB0;'>DISTINTA DIGITALE LIVE</div>", unsafe_allow_html=True)
    
    # PROTEZIONE INTEGRATA: Se il file non esiste o è corrotto, mostra l'attesa senza rompere l'app
    if not os.path.exists("distinta_corrente.json") or os.path.getsize("distinta_corrente.json") == 0:
        st.write("")
        st.warning("⌛ DISTINTA IN AGGIORNAMENTO\n\nLa segreteria sta caricando le distinte ufficiali della partita. Riprova tra qualche istante o rinfresca la pagina.")
        return
        
    try:
        with open("distinta_corrente.json", "r", encoding="utf-8") as f:
            dati = json.load(f)
            
        info = dati["info_gara"]
        st.markdown(f"<div class='info-match'>🏆 {info.get('campionato', '')} | 📅 {info.get('data', '')}<br>🏁 Arbitro: {info.get('arbitro', '')}</div>", unsafe_allow_html=True)
        
        # Render Squadra Casa
        st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
        st.markdown(f"<div class='nome-squadra'>🏠 {dati['casa'].get('squadra', 'SQUADRA CASA')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='allenatore'>All. {dati['casa'].get('allenatore', '')}</div>", unsafe_allow_html=True)
        for g in dati["casa"].get("giocatori", []):
            if g.get("GIOCATORE", "").strip():
                st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g['N°']}</span><span class='nome-giocatore'>{g['GIOCATORE']}</span><span class='anno-giocatore'>{g['ANNO']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Render Squadra Ospite
        st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
        st.markdown(f"<div class='nome-squadra'>🚀 {dati['ospite'].get('squadra', 'SQUADRA OSPITE')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='allenatore'>All. {dati['ospite'].get('allenatore', '')}</div>", unsafe_allow_html=True)
        for g in dati["ospite"].get("giocatori", []):
            if g.get("GIOCATORE", "").strip():
                st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g['N°']}</span><span class='nome-giocatore'>{g['GIOCATORE']}</span><span class='anno-giocatore'>{g['ANNO']}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    except Exception:
        st.warning("⌛ Aggiornamento liste in corso da parte della segreteria...")
        return
        
    st.markdown("<p style='text-align:center; color:#A0AEC0; font-size:11px;'>Servizio Distinte Ufficiali Azzurra Due Carrare</p>", unsafe_allow_html=True)
