import streamlit as st
import json
import os

def mostra_pagina_formazione():
    """Scarica il file JSON e mostra la formazione se rileva il parametro 'match' nell'URL"""
    params = {}
    try:
        # Recupero universale e robusto dei parametri URL
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
        # Se Streamlit restituisce una lista (es. ['a1b2c3']), estraiamo il primo elemento stringa
        if isinstance(valore, list):
            match_id = valore[0] if len(valore) > 0 else None
        else:
            match_id = valore
    
    # SE IL PARAMETRO È PRESENTE, ABBIAMO INTERCETTATO LO SMARTPHONE!
    if match_id:
        try:
            percorso_file = os.path.join("match_data", f"{match_id}.json")
            
            if not os.path.exists(percorso_file):
                st.error("Formazione non trovata. Il codice potrebbe essere scaduto o l'applicazione è stata riavviata.")
                st.stop()
                
            with open(percorso_file, "r", encoding="utf-8") as f_in:
                pacchetto = json.load(f_in)
            
            # Estrazione dei dati corretti dal dizionario salvato
            info = pacchetto["info"]   # [campionato, data, arbitro, ass1, ass2]
            casa = pacchetto["casa"]   # [squadra, allenatore, giocatori_lista]
            ospite = pacchetto["ospite"] # [squadra, allenatore, giocatori_lista]
            
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
            st.markdown(f'<p class="sub-title">🏆 {info[0]}<br>📅 {info[1]}</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Colonna Squadra in Casa
            with col1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {casa[1]}</p></div>', unsafe_allow_html=True)
                for g in casa[2]: # g è la lista del singolo giocatore: [Numero, Nome, Anno]
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
            
            # Colonna Squadra Ospite
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite[0]}</p>'
                            f'<p class="all-name"><b>All:</b> {ospite[1]}</p></div>', unsafe_allow_html=True)
                for g in ospite[2]:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g[0]}</div>'
                                f'<div class="player-name">{g[1]}</div>'
                                f'<div class="player-year">{g[2]}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 **Arbitro:** {info[2]} | **Assistenti:** {info[3]} - {info[4]}")
            st.stop() # FORZATURA: Blocca l'applicazione impedendo il caricamento della pagina iniziale
        except Exception as e:
            st.error(f"Errore grafico durante il rendering della formazione: {e}")
            st.stop()
