import streamlit as st
import pandas as pd

def applica_shift(chiave_griglia, riga, direzione):
    df = st.session_state[chiave_griglia].copy().reset_index()
    idx = riga - 1
    if direzione == "giù":
        nuova_riga = pd.DataFrame([{"N°": riga, "GIOCATORE": "", "ANNO": ""}])
        df_nuovo = pd.concat([df.iloc[:idx], nuova_riga, df.iloc[idx:19]]).reset_index(drop=True)
    elif direzione == "su":
        riga_vuota = pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])
        df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], riga_vuota]).reset_index(drop=True)
    df_nuovo["N°"] = range(1, 21)
    st.session_state[chiave_griglia] = df_nuovo.set_index("N°")
    st.rerun()

def render_colonna_squadra(label_titolo, chiave_griglia, default_all):
    """Rende la colonna squadra senza estrarre il nome dall'AI, lasciandolo all'utente"""
    st.subheader(label_titolo)
    
    # Il nome della società ora è gestito con uno stato persistente pulito che l'utente compila a mano
    chiave_nome_societa = f"nome_societa_{chiave_griglia}"
    if chiave_nome_societa not in st.session_state:
        st.session_state[chiave_nome_societa] = ""
        
    nome = st.text_input(f"Nome Società {label_titolo}", value=st.session_state[chiave_nome_societa], key=f"n_{chiave_griglia}")
    st.session_state[chiave_nome_societa] = nome
    
    alln = st.text_input(f"Allenatore {label_titolo}", value=default_all, key=f"a_{chiave_griglia}")
    
    st.session_state[chiave_griglia] = st.data_editor(st.session_state[chiave_griglia], key=f"ed_{chiave_griglia}", use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        riga_scelta = st.selectbox("🎯 Riga", options=list(range(1, 21)), index=12, key=f"sel_{chiave_griglia}")
    with c2:
        st.write("<div style='padding-top: 24px;'></div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("⬇️", key=f"down_{chiave_griglia}", use_container_width=True):
                applica_shift(chiave_griglia, riga_scelta, "giù")
        with b2:
            if st.button("⬆️", key=f"up_{chiave_griglia}", use_container_width=True):
                applica_shift(chiave_griglia, riga_scelta, "su")
                
    return {"squadra": nome, "allenatore": alln}
