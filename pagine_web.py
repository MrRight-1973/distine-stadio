import streamlit as st
import json
import base64

def mostra_pagina_formazione():
    """Mostra una splendida pagina web ottimizzata per smartphone se rileva i dati nell'URL"""
    
    # STRATEGIA DI RECUPERO UNIVERSALE: Prova prima il metodo moderno, poi il dizionario, poi la versione sperimentale
    params = {}
    try:
        if hasattr(st, "query_parameters"):
            # Gestione come dizionario o come callable a seconda della versione esatta di Streamlit
            if callable(st.query_parameters):
                params = st.query_parameters()
            else:
                params = st.query_parameters
        else:
            params = st.experimental_get_query_params()
    except Exception:
        try:
            params = st.experimental_get_query_params()
        except Exception:
            params = {}

    # Estraiamo il valore del parametro 'match' gestendo sia il formato stringa che il formato lista (vecchio formato query)
    match_param = None
    if "match" in params:
        valore = params["match"]
        match_param = valore[0] if isinstance(valore, list) else valore
    
    if match_param:
        try:
            # 1. Decodifichiamo i dati compressi passati dal QR Code
            dati_json = base64.b64decode(match_param).decode('utf-8')
            match_data = json.loads(dati_json)
            
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
            
            # 2. Intestazione della pagina
            st.markdown('<p class="main-title">⚽ FORMAZIONI DI GARA LND</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="sub-title">🏆 {match_data["info"]["campionato"]} | 📅 {match_data["info"]["data"]}</p>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # 3. Colonna Squadra in Casa
            with col1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {match_data["casa"]["squadra"]}</p>'
                            f'<p class="all-name"><b>All:</b> {match_data["casa"]["allenatore"]}</p></div>', unsafe_allow_html=True)
                for g in match_data["casa"]["giocatori"]:
                    if g.get("GIOCATORE"): # Mostra solo le righe compilate
                        st.markdown(f'<div class="player-row"><div class="player-num">{g.get("N°")}</div>'
                                    f'<div class="player-name">{g.get("GIOCATORE")}</div>'
                                    f'<div class="player-year">{g.get("ANNO")}</div></div>', unsafe_allow_html=True)
            
            # 4. Colonna Squadra Ospite
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {match_data["ospite"]["squadra"]}</p>'
                            f'<p class="all-name"><b>All:</b> {match_data["ospite"]["allenatore"]}</p></div>', unsafe_allow_html=True)
                for g in match_data["ospite"]["giocatori"]:
                    if g.get("GIOCATORE"):
                        st.markdown(f'<div class="player-row"><div class="player-num">{g.get("N°")}</div>'
                                    f'<div class="player-name">{g.get("GIOCATORE")}</div>'
                                    f'<div class="player-year">{g.get("ANNO")}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 Arbitro: {match_data['info'].get('arbitro', '')} | Assistenti: {match_data['info'].get('assistente1', '')} - {match_data['info'].get('assistente2', '')}")
            st.stop() # Blocca l'applicazione mostrando esclusivamente lo schermo per il telefono
        except Exception as e:
            st.error("Impossibile caricare i dati della formazione. Il link potrebbe essere corrotto.")
