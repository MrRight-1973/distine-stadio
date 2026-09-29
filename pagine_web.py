import streamlit as st
import json
import requests

def mostra_pagina_formazione():
    """Scarica i dati dal cloud usando la chiave corta dell'URL e mostra la formazione sul telefono"""
    params = {}
    try:
        if hasattr(st, "query_parameters"):
            if callable(st.query_parameters): params = st.query_parameters()
            else: params = st.query_parameters
        else: params = st.experimental_get_query_params()
    except Exception:
        try: params = st.experimental_get_query_params()
        except Exception: params = {}

    match_id = None
    if "match" in params:
        valore = params["match"]
        match_id = valore if isinstance(valore, list) else valore
    
    # Se nell'URL c'è la chiave corta della partita, scarichiamo i dati e mostriamo lo schermo azzurro
    if match_id:
        try:
            # Scarichiamo il JSON della partita memorizzato nel cloud storage
            url_storage = f"https://keyvalue.xyz{match_id}"
            r_cloud = requests.get(url_storage)
            
            if r_cloud.status_code != 200:
                st.error("Formazione non trovata o scaduta nel database cloud.")
                st.stop()
                
            pacchetto = r_cloud.json()
            
            # Assegnazione dei dati scaricati
            info_lista = pacchetto["info"]
            casa_lista = pacchetto["casa"]
            ospite_lista = pacchetto["ospite"]
            
            # --- STILE GRAFICO ASD AZZURRA DUE CARRARE ---
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
            
            # Colonna Casa
            with col1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa_lista[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {casa_lista[1]}</p></div>', unsafe_allow_html=True)
                for g in casa_lista[2]: # Scorre la lista [Numero, Nome, Anno]
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
            
            # Colonna Ospite
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite_lista[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {ospite_lista[1]}</p></div>', unsafe_allow_html=True)
                for g in ospite_lista[2]:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 Arbitro: {info_lista[2]} | Assistenti: {info_lista[3]} - {info_lista[4]}")
            st.stop() # Interrompe Streamlit mostrando solo lo schermo mobile
        except Exception as e:
            st.error(f"Errore di connessione al database formazioni: {e}")
            st.stop()
