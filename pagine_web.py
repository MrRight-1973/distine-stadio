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
        else:
            params = st.experimental_get_query_params()
    except Exception:
        try: params = st.experimental_get_query_params()
        except Exception: params = {}

    match_id = None
    if "match" in params:
        valore = params["match"]
        if isinstance(valore, list):
            match_id = valore if len(valore) > 0 else None
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
            
            # Estrazione dei dati corretti dal dizionario salvato tramite gli indici corretti
            info = pacchetto["info"]     # [campionato, data, arbitro, ass1, ass2]
            casa = pacchetto["casa"]     # [squadra, allenatore, giocatori_lista]
            ospite = pacchetto["ospite"] # [squadra, allenatore, giocatori_lista]
            
            # --- STILE GRAFICO ASD AZZURRA DUE CARRARE ---
            st.markdown("""
                <style>
                .main-title { color: #0096FF; text-align: center; font-size: 26px; font-weight: bold; margin-bottom: 2px; }
                .sub-title { color: #555; text-align: center; font-size: 15px; margin-bottom: 20px; line-height: 1.4; }
                .card-team { background-color: #E6F2FF; border-left: 5px solid #0096FF; padding: 12px; border-radius: 4px; margin-bottom: 12px; }
                .team-name { color: #0096FF; font-size: 20px; font-weight: bold; margin: 0; }
                .all-name { color: #333; font-size: 14px; margin: 4px 0 0 0; }
                .player-row { display: flex; padding: 7px 0; border-bottom: 1px solid #E2E8F0; font-size: 15px; }
                .player-num { width: 35px; font-weight: bold; color: #0096FF; }
                .player-name { flex-grow: 1; color: #1A202C; }
                .player-year { width: 50px; color: #718096; text-align: right; }
                .info-footer { background-color: #F7FAFC; padding: 10px; border-radius: 4px; text-align: center; font-size: 13px; color: #4A5568; margin-top: 20px; }
                </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<p class="main-title">⚽ FORMAZIONI DI GARA LND</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="sub-title">🏆 <b>{info}</b><br>📅 Data: {info}</p>', unsafe_allow_html=True)
            
            col_m1, col_m2 = st.columns(2)
            
            # Colonna Squadra in Casa
            with col_m1:
                st.markdown(f'<div class="card-team"><p class="team-name">🏠 {casa}</p>'
                            f'<p class="all-name"><b>Allenatore:</b> {casa}</p></div>', unsafe_allow_html=True)
                for g in casa: # g è la lista del singolo giocatore: [Numero, Nome, Anno]
                    st.markdown(f'<div class="player-row"><div class="player-num">{g}</div>'
                                f'<div class="player-name">{g}</div>'
                                f'<div class="player-year">{g}</div></div>', unsafe_allow_html=True)
            
            # Colonna Squadra Ospite
            with col_m2:
                st.markdown(f'<div class="card-team"><p class="team-name">🚀 {ospite}</p>'
                            f'<p class="all-name"><b>Allenatore:</b> {ospite}</p></div>', unsafe_allow_html=True)
                for g in ospite:
                    st.markdown(f'<div class="player-row"><div class="player-num">{g}</div>'
                                f'<div class="player-name">{g}</div>'
                                f'<div class="player-year">{g}</div></div>', unsafe_allow_html=True)
                        
            st.markdown(f'<div class="info-footer">🏁 <b>Arbitro:</b> {info} | 🚩 <b>Assistenti:</b> {info} - {info}</div>', unsafe_allow_html=True)
            
            # WhatsApp Button per i dirigenti
            testo_condivisione = f"Formazioni {casa} vs {ospite} del {info}: https://streamlit.app{match_id}"
            st.write("")
            st.page_link(f"https://whatsapp.com{testo_condivisione}", label="📲 Condividi Formazione su WhatsApp", icon="💬")
            
            st.stop() # Blocco forzato: mostra solo lo schermo mobile azzurro
        except Exception as e:
            st.error(f"Errore grafico durante il rendering della formazione: {e}")
            st.stop()
