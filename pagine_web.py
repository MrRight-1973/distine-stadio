import streamlit as st
import json
import base64

import streamlit as st
import json
import base64

def mostra_pagina_formazione():
    """Mostra una splendida pagina web ottimizzata per smartphone se rileva i dati nell'URL"""
    # CORREZIONE: Aggiunte le parentesi tonde () per richiamare correttamente la funzione di Streamlit
    params = st.query_parameters() 
    
    if "match" in params:
        try:
            # 1. Decodifichiamo i dati compressi passati dal QR Code
            dati_compressi = params["match"]

            
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
                    if g["GIOCATORE"]: # Mostra solo le righe compilate
                        st.markdown(f'<div class="player-row"><div class="player-num">{g["N°"]}</div>'
                                    f'<div class="player-name">{g["GIOCATORE"]}</div>'
                                    f'<div class="player-year">{g["ANNO"]}</div></div>', unsafe_allow_html=True)
            
            # 4. Colonna Squadra Ospite
            with col2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {match_data["ospite"]["squadra"]}</p>'
                            f'<p class="all-name"><b>All:</b> {match_data["ospite"]["allenatore"]}</p></div>', unsafe_allow_html=True)
                for g in match_data["ospite"]["giocatori"]:
                    if g["GIOCATORE"]:
                        st.markdown(f'<div class="player-row"><div class="player-num">{g["N°"]}</div>'
                                    f'<div class="player-name">{g["GIOCATORE"]}</div>'
                                    f'<div class="player-year">{g["ANNO"]}</div></div>', unsafe_allow_html=True)
                        
            st.markdown("---")
            st.caption(f"🏁 Arbitro: {match_data['info']['arbitro']} | Assistenti: {match_data['info']['assistente1']} - {match_data['info']['assistente2']}")
            st.stop() # Blocca il resto del caricamento per mostrare SOLO la formazione
        except Exception as e:
            st.error("Impossibile caricare i dati della formazione. Il link potrebbe essere corrotto.")
