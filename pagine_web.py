import streamlit as st
import json
import base64
import zlib

def mostra_pagina_formazione():
    """Mostra la pagina web per lo smartphone decodificando i dati compressi dal QR"""
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
            # Decompressione sicura dei dati URL-Safe
            dati_binari = base64.urlsafe_b64decode(match_param)
            stringa_json = zlib.decompress(dati_binari).decode('utf-8')
            pacchetto = json.loads(stringa_json)
            
            # Estrazione dei dati in base alla nuova struttura a indici
            info_lista = pacchetto["i"]
            casa_lista = pacchetto["c"]
            ospite_lista = pacchetto["o"]
            
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
            
            st.markdown('<p class="main-title">⚽ FORMAZIONI DI GARA LND</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="sub-title">🏆 {info_lista[0]} | 📅 {info_lista[1]}</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa_lista[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {casa_lista[1]}</p></div>', unsafe_allow_html=True)
                for g in casa_lista[2]: # g è una lista tipo [Numero, Nome, Anno]
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite_lista[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {ospite_lista[1]}</p></div>', unsafe_allow_html=True)
                for g in ospite_lista[2]:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 Arbitro: {info_lista[2]} | Assistenti: {info_lista[3]} - {info_lista[4]}")
            st.stop()
        except Exception as e:
            st.error(f"Errore durante il caricamento dei dati: {e}")
            st.stop()
