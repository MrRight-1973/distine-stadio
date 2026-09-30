import streamlit as st
import json
import os

def render_pagina_spettatori():
    """Mostra la distinta live per la modalità classica"""
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
        .spazio-sicurezza-footer { height: 100px; margin-top: 20px; text-align: center; color: #A0AEC0; font-size: 12px; border-top: 1px dashed #CBD5E0; padding-top: 15px; }
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
        mostra_liste_html(dati)
    except:
        return

def render_html_puro_tifosi():
    """Inietta una pagina HTML nativa, eliminando alla radice loghi e tasto fullscreen"""
    if not os.path.exists("distinta_corrente.json") or os.path.getsize("distinta_corrente.json") == 0:
        st.markdown("<h2 style='text-align:center;font-family:sans-serif;color:#4A5568;padding-top:50px;'>⌛ Distinta in corso di aggiornamento...</h2>", unsafe_allow_html=True)
        return
        
    with open("distinta_corrente.json", "r", encoding="utf-8") as f:
        dati = json.load(f)
        
    info = dati.get("info_gara", {})
    casa = dati.get("casa", {})
    ospite = dati.get("ospite", {})
    
    # Generiamo un blocco HTML puro che sostituisce l'intera pagina del telefono
    html_spettatore = f"""
    <div style='font-family:-apple-system,BlinkMacSystemFont,sans-serif; background-color:#F0F4F8; margin:-1rem; padding:15px; min-height:100vh;'>
        <div style='text-align:center; color:#1A365D; font-size:24px; font-weight:bold; margin-bottom:5px;'>⚽ AZZURRA DUE CARRARE</div>
        <div style='text-align:center; color:#2B6CB0; font-size:16px; font-weight:bold; margin-bottom:5px;'>DISTINTA LIVE SPECIALE</div>
        <div style='text-align:center; color:#4A5568; font-size:13px; margin-bottom:20px;'>🏆 {info.get('campionato','')} | 📅 {info.get('data','')} <br>🏁 Arbitro: {info.get('arbitro','')}</div>
        
        <!-- CASA -->
        <div style='background-color:white; padding:15px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:15px;'>
            <div style='color:#2B6CB0; font-size:18px; font-weight:bold; border-bottom:2px solid #E2E8F0; padding-bottom:5px; margin-bottom:10px;'>🏠 {casa.get('squadra','')}</div>
            <div style='font-style:italic; color:#4A5568; font-size:13px; margin-bottom:10px;'>All. {casa.get('allenatore','')}</div>
    """
    for g in casa.get("giocatori", []):
        if g.get("GIOCATORE", "").strip():
            html_spettatore += f"<div style='display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid #EDF2F7; font-size:15px;'><span style='font-weight:bold; color:#2B6CB0; width:25px;'>{g.get('N°','')}</span><span style='flex-grow:1; text-align:left; padding-left:5px; color:#2D3748;'>{g.get('GIOCATORE','')}</span><span style='color:#A0AEC0; width:40px; text-align:right;'>{g.get('ANNO','')}</span></div>"
            
    html_spettatore += f"""
        </div>
        <!-- OSPITE -->
        <div style='background-color:white; padding:15px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:15px;'>
            <div style='color:#2B6CB0; font-size:18px; font-weight:bold; border-bottom:2px solid #E2E8F0; padding-bottom:5px; margin-bottom:10px;'>🚀 {ospite.get('squadra','')}</div>
            <div style='font-style:italic; color:#4A5568; font-size:13px; margin-bottom:10px;'>All. {ospite.get('allenatore','')}</div>
    """
    for g in ospite.get("giocatori", []):
        if g.get("GIOCATORE", "").strip():
            html_spettatore += f"<div style='display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid #EDF2F7; font-size:15px;'><span style='font-weight:bold; color:#2B6CB0; width:25px;'>{g.get('N°','')}</span><span style='flex-grow:1; text-align:left; padding-left:5px; color:#2D3748;'>{g.get('GIOCATORE','')}</span><span style='color:#A0AEC0; width:40px; text-align:right;'>{g.get('ANNO','')}</span></div>"
            
    html_spettatore += """
        </div>
        <div style='text-align:center; margin-top:20px; color:#A0AEC0; font-size:11px;'>⚽ Azzurra Due Carrare - Grafica Pulita</div>
    </div>
    """
    st.markdown(html_spettatore, unsafe_allow_html=True)

def mostra_liste_html(dati):
    info = dati.get("info_gara", {})
    st.markdown(f"<div class='info-match'>🏆 {info.get('campionato', '')} | 📅 {info.get('data', '')}<br>🏁 Arbitro: {info.get('arbitro', '')}</div>", unsafe_allow_html=True)
    
    casa_dati = dati.get("casa", {})
    st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-squadra'><div class='nome-squadra'>🏠 {casa_dati.get('squadra', 'SQUADRA CASA')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='allenatore'>All. {casa_dati.get('allenatore', '')}</div>", unsafe_allow_html=True)
    for g in casa_dati.get("giocatori", []):
        if g.get("GIOCATORE", "").strip():
            st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g.get('N°', '')}</span><span class='nome-giocatore'>{g.get('GIOCATORE', '')}</span><span class='anno-giocatore'>{g.get('ANNO', '')}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    ospite_dati = dati.get("ospite", {})
    st.markdown("<div class='card-squadra'>", unsafe_allow_html=True)
    st.markdown(f"<div class='nome-squadra'>🚀 {ospite_dati.get('squadra', 'SQUADRA OSPITE')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='allenatore'>All. {ospite_dati.get('allenatore', '')}</div>", unsafe_allow_html=True)
    for g in ospite_dati.get("giocatori", []):
        if g.get("GIOCATORE", "").strip():
            st.markdown(f"<div class='riga-giocatore'><span class='num-maglia'>{g.get('N°', '')}</span><span class='nome-giocatore'>{g.get('GIOCATORE', '')}</span><span class='anno-giocatore'>{g.get('ANNO', '')}</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='spazio-sicurezza-footer'>⚽ Azzurra Due Carrare Live</div>", unsafe_allow_html=True)
