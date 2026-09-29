import streamlit as st
import json
import os

def mostra_pagina_formazione():
    """Legge il file JSON dal server usando l'ID corto nell'URL e mostra la formazione"""
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
        if isinstance(match_id, list) and len(match_id) > 0:
            match_id = match_id
    
    if match_id:
        try:
            # Costruiamo il percorso per andare a leggere il file sul server
            percorso_file = os.path.join("match_data", f"{match_id}.json")
            
            if not os.path.exists(percorso_file):
                st.error("Formazione non trovata. Il codice potrebbe essere scaduto o l'app è stata riavviata.")
                st.stop()
                
            with open(percorso_file, "r", encoding="utf-8") as f_in:
                pacchetto = json.load(f_in)
            
            # Assegnazione dati
            info_lista = pacchetto["info"]
            casa_lista = pacchetto["casa"]
            ospite_lista = pacchetto["ospite"]
            
            # --- STILE GRAFICO ASD AZZURRA DUE CARRARE ---
            st.markdown("""
                <style>
                .main-title { color: #0096FF; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 2px; }
                .sub-title { color: #555; text-align: center; font-size: 14px; margin-bottom: 18px; }
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
            st.markdown(f'<p class="sub-title">🏆 {info_lista}<br>📅 {info_lista}</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Colonna Casa
            with col1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa_lista}</p>'
                            f'<p class="all-name"><b>All:</b> {casa_lista}</p></div>', unsafe_allow_html=True)
                for g in casa_lista:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g}</div>'
                                f'<div class="player-name">{g}</div>'
                                f'<div class="player-year">{g}</div></div>', unsafe_allow_html=True)
            
            # Colonna Ospite
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite_lista}</p>'
                            f'<p class="all-name"><b>All:</b> {ospite_lista}</p></div>', unsafe_allow_html=True)
                for g in ospite_lista:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g}</div>'
                                f'<div class="player-name">{g}</div>'
                                f'<div class="player-year">{g}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 **Arbitro:** {info_lista} | **Assistenti:** {info_lista} - {info_lista}")
            st.stop()
        except Exception as e:
            st.error(f"Errore di lettura della formazione: {e}")
            st.stop()
