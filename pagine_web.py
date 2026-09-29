import streamlit as st
import json
import base64
import zlib

def mostra_pagina_formazione():
    """Mostra una splendida pagina web ottimizzata per smartphone decodificando i dati compressi"""
    params = {}
    try:
        if hasattr(st, "query_parameters"):
            if callable(st.query_parameters): params = st.query_parameters()
            else: params = st.query_parameters
        else: params = st.experimental_get_query_params()
    except Exception:
        try: params = st.experimental_get_query_params()
        except Exception: params = {}

    match_param = None
    if "match" in params:
        valore = params["match"]
        match_param = valore[0] if isinstance(valore, list) else valore
    
    if match_param:
        try:
            # DECOMPRESSIONE DEI DATI ULTRASHORT
            dati_binari = base64.urlsafe_b64decode(match_param)
            stringa_json = zlib.decompress(dati_binari).decode('utf-8')
            pacchetto_micro = json.loads(stringa_json)
            
            # Ricostruiamo la struttura leggibile per l'interfaccia grafica mobile
            info = pacchetto_micro["i"]
            casa = pacchetto_micro["c"]
            ospite = pacchetto_micro["o"]
            
            # --- STILE GRAFICO AZZURRA DUE CARRARE ---
            st.markdown("""
                <style>
                .main-title { color: #0096FF; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 2px; }
                .sub-title { color: #555; text-align: center; font-size: 14px; margin-bottom: 20px; }
                .card-team { background-color: #E6F2FF; border-left: 5px solid #0096FF; padding: 12px; border-radius: 4px; margin-bottom: 10px; }
                .team-name { color: #0096FF; font-size: 18px; font-weight: bold; margin: 0; }
                .all-name { color: #333; font-size: 13px; margin: 2px 0 0 0; }
                .player-row { display: flex; padding: 6px 0; border-bottom: 1px solid #E2E8F0; font-size: 14px; }
                .player-num { width: 35px; font-weight: bold; color: #0096FF; }
                .player-name { flex-grow: 1; color: #1A202C; }
                .player-year { width: 50px; color: #718096; text-align: right; }
                </style>
            """, unsafe_allow_html=True)
            
            # Intestazione della pagina
            st.markdown('<p class="main-title">⚽ FORMAZIONI DI GARA LND</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="sub-title">🏆 {info[0]} | 📅 {info[1]}</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Squadra in Casa
            with col1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {casa[1]}</p></div>', unsafe_allow_html=True)
                for g in casa[2]: # g è una lista tipo: [Numero, Nome, Anno]
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
            
            # Squadra Ospite
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {ospite[1]}</p></div>', unsafe_allow_html=True)
                for g in ospite[2]:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 Arbitro: {info[2]} | Assistenti: {info[3]} - {info[4]}")
            st.stop()
        except Exception as e:
            st.error("Impossibile caricare i dati della formazione. Il link potrebbe essere corrotto.")
