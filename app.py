import streamlit as st
import io
import qrcode
import requests
import base64
import json
import zlib
import pandas as pd
from estrattore import analizza_distinta, genera_pdf, pulisci_testo

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

# --- INTERCETTAZIONE LINK SPETTATORI DA QR CODE (MOBILE FRIENDLY) ---
query_params = st.query_params
if "match" in query_params:
    try:
        # 1. Recupera e decodifica la stringa compressa Base64 dall'URL
        stringa_compressa = query_params["match"]
        compresso = base64.urlsafe_b64decode(stringa_compressa.encode('utf-8'))
        json_string = zlib.decompress(compresso).decode('utf-8')
        dati_match = json.loads(json_string)
        
        # 2. Mostra un'interfaccia mobile elegante e pulita per i tifosi allo stadio
        st.title("⚽ Distinta Digitale Ufficiale")
        st.subheader(f"🏆 {dati_match.get('c', 'CAMPIONATO LND')}")
        st.markdown(f"📅 *Gara del:* **{dati_match.get('d', 'N.D.')}**")
        
        st.markdown("---")
        
        # Layout a due colonne ottimizzato per smartphone
        col_casa, col_ospite = st.columns(2)
        with col_casa:
            st.markdown(f"🏠 **CASA:** {dati_match.get('s1', 'SQUADRA LOCALE')}")
            # Se vuoi estendere e mostrare l'intera lista ti basterà salvarla nel dizionario al passaggio 1
            st.info("Formazione ufficiale disponibile a breve sui tabelloni.")
            
        with col_ospite:
            st.markdown(f"🚀 **OSPITE:** {dati_match.get('s2', 'SQUADRA OSPITE')}")
            st.info("Formazione ufficiale disponibile a breve sui tabelloni.")
            
        st.markdown("---")
        st.caption("Servizio digitale offerto dal Centro Gestione Distinte Gara.")
        
        # Blocca l'esecuzione qui in modo che lo spettatore non veda il caricamento dei file della Fase 1
        st.stop()
        
    except Exception as e_decode:
        st.error(f"Impossibile decodificare i dati del match: {e_decode}")

st.title("⚽ Centro Gestione Distinte Gara Gestionale")
st.write("Carica i fogli gara ed effettua modifiche o slittamenti istantanei sulle liste.")

api_key_openai = st.secrets.get("OPENAI_API_KEY")

if "griglia_casa" not in st.session_state:
    st.session_state["griglia_casa"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")
if "griglia_ospite" not in st.session_state:
    st.session_state["griglia_ospite"] = pd.DataFrame([{"N°": i, "GIOCATORE": "", "ANNO": ""} for i in range(1, 21)]).set_index("N°")

col_f1, col_f2 = st.columns(2)
with col_f1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
with col_f2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")

if file_casa and file_ospite:
    if "dati_mappati" not in st.session_state:
        if st.button("🔍 Fase 1: Esegui Scansione AI delle Immagini", type="primary"):
            with st.spinner("L'AI sta leggendo le distinte..."):
                try:
                    casa_raw = analizza_distinta(file_casa, "CASA", api_key_openai)
                    ospite_raw = analizza_distinta(file_ospite, "OSPITE", api_key_openai)
                    
                    st.session_state["griglia_casa"] = pd.DataFrame(casa_raw["giocatori"]).set_index("N°")
                    st.session_state["griglia_ospite"] = pd.DataFrame(ospite_raw["giocatori"]).set_index("N°")
                    st.session_state["macro_info"] = {"campionato": casa_raw["campionato"], "data": casa_raw["data"], "squadra_casa": casa_raw["squadra"], "all_casa": casa_raw["allenatore"], "squadra_ospite": ospite_raw["squadra"], "all_ospite": ospite_raw["allenatore"]}
                    st.session_state["dati_mappati"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore durante l'analisi visiva: {e}")

if "dati_mappati" in st.session_state:
    st.markdown("---")
    st.header("✏️ Fase 2: Controllo, Correzione e Funzioni di Shift")
    
    info = st.session_state["macro_info"]
    
    st.subheader("🏁 Informazioni Generali Match")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        edit_campionato = st.text_input("🏆 Campionato / Categoria", value=info["campionato"])
        edit_arbitro = st.text_input("🏁 Arbitro (Nome e Cognome)", value="")
        edit_ass1 = st.text_input("🚩 Assistente 1", value="")
    with c_g2:
        edit_data = st.text_input("📅 Data Partita", value=info["data"])
        st.write("")
        edit_ass2 = st.text_input("🚩 Assistente 2", value="")
        
    st.markdown("---")
    
    # Griglia principale per le due squadre
    c_sq1, c_sq2 = st.columns(2)
    
    opzioni_righe = [i for i in range(1, 21)]
    
    # --- GESTIONE SQUADRA CASA ---
    with c_sq1:
        st.subheader("🏠 SQUADRA CASA")
        edit_nome_casa = st.text_input("Nome Società Ospitante", value=info["squadra_casa"])
        edit_all_casa = text_all_casa = st.text_input("Allenatore Ospitante", value=info["all_casa"])
        
        st.session_state["griglia_casa"] = st.data_editor(st.session_state["griglia_casa"], key="editor_casa_current", use_container_width=True, hide_index=False)
        
        # Sotto-griglia bilanciata per i controlli Casa
        c_ctrl_c1, c_ctrl_c2 = st.columns([1, 1])
        with c_ctrl_c1:
            riga_scelta_casa = st.selectbox("🎯 Riga (Casa)", options=opzioni_righe, index=12, key="sel_casa")
        with c_ctrl_c2:
            st.write(" <div style='padding-top: 24px;'></div>", unsafe_allow_html=True) # Allinea i pulsanti verticalmente al selectbox
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("⬇️", key="shift_down_casa", use_container_width=True, help="Slitta in basso"):
                    df = st.session_state["griglia_casa"].copy().reset_index()
                    idx = riga_scelta_casa - 1
                    nuova_riga = pd.DataFrame([{"N°": riga_scelta_casa, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], nuova_riga, df.iloc[idx:19]]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_casa"] = df_nuovo.set_index("N°")
                    st.rerun()
            with c_btn2:
                if st.button("⬆️", key="shift_up_casa", use_container_width=True, help="Slitta in alto"):
                    df = st.session_state["griglia_casa"].copy().reset_index()
                    idx = riga_scelta_casa - 1
                    riga_vuota_finale = pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], riga_vuota_finale]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_casa"] = df_nuovo.set_index("N°")
                    st.rerun()

    # --- GESTIONE SQUADRA OSPITE ---
    with c_sq2:
        st.subheader("🚀 SQUADRA OSPITE")
        edit_nome_ospite = st.text_input("Nome Società Ospite", value=info["squadra_ospite"])
        edit_all_ospite = st.text_input("Allenatore Ospite", value=info["all_ospite"])
        
        st.session_state["griglia_ospite"] = st.data_editor(st.session_state["griglia_ospite"], key="editor_ospite_current", use_container_width=True, hide_index=False)
        
        # Sotto-griglia bilanciata per i controlli Ospite (Speculare alla Casa)
        c_ctrl_o1, c_ctrl_o2 = st.columns([1, 1])
        with c_ctrl_o1:
            riga_scelta_ospite = st.selectbox("🎯 Riga (Ospite)", options=opzioni_righe, index=12, key="sel_ospite")
        with c_ctrl_o2:
            st.write(" <div style='padding-top: 24px;'></div>", unsafe_allow_html=True) # Allinea i pulsanti verticalmente al selectbox
            o_btn1, o_btn2 = st.columns(2)
            with o_btn1:
                if st.button("⬇️", key="shift_down_ospite", use_container_width=True, help="Slitta in basso"):
                    df = st.session_state["griglia_ospite"].copy().reset_index()
                    idx = riga_scelta_ospite - 1
                    nuova_riga = pd.DataFrame([{"N°": riga_scelta_ospite, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], nuova_riga, df.iloc[idx:19]]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_ospite"] = df_nuovo.set_index("N°")
                    st.rerun()
            with o_btn2:
                if st.button("⬆️", key="shift_up_ospite", use_container_width=True, help="Slitta in alto"):
                    df = st.session_state["griglia_ospite"].copy().reset_index()
                    idx = riga_scelta_ospite - 1
                    riga_vuota_finale = pd.DataFrame([{"N°": 20, "GIOCATORE": "", "ANNO": ""}])
                    df_nuovo = pd.concat([df.iloc[:idx], df.iloc[idx+1:], riga_vuota_finale]).reset_index(drop=True)
                    df_nuovo["N°"] = range(1, 21)
                    st.session_state["griglia_ospite"] = df_nuovo.set_index("N°")
                    st.rerun()

    # --- GENERAZIONE PDF FINALE INTERNA (ZERO ERRORI DI RETE) ---
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code Integrato", type="primary"):
        with st.spinner("Generazione del foglio di gara definitivo in corso..."):
            try:
                giocatori_casa_salvati = st.session_state["griglia_casa"].reset_index().to_dict(orient="records")
                giocatori_ospite_salvati = st.session_state["griglia_ospite"].reset_index().to_dict(orient="records")
                
                squadra_casa_corretta = {
                    "squadra": pulisci_testo(edit_nome_casa),
                    "allenatore": pulisci_testo(edit_all_casa),
                    "giocatori": giocatori_casa_salvati
                }
                squadra_ospite_corretta = {
                    "squadra": pulisci_testo(edit_nome_ospite),
                    "allenatore": pulisci_testo(edit_all_ospite),
                    "giocatori": giocatori_ospite_salvati
                }
                info_gara_corrette = {
                    "campionato": pulisci_testo(edit_campionato),
                    "data": pulisci_testo(edit_data),
                    "arbitro": pulisci_testo(edit_arbitro),
                    "assistente1": pulisci_testo(edit_ass1),
                    "assistente2": pulisci_testo(edit_ass2)
                }
                
                # 1. Genera la struttura iniziale dei dati in una stringa compatta e sicura per gli URL
                import zlib
                dati_per_qr = {
                    "c": info_gara_corrette["campionato"],
                    "d": info_gara_corrette["data"],
                    "s1": squadra_casa_corretta["squadra"],
                    "s2": squadra_ospite_corretta["squadra"]
                }
                
                # Compressione per mantenere il QR code leggero e facile da scansionare dallo smartphone
                json_string = json.dumps(dati_per_qr).encode('utf-8')
                compresso = zlib.compress(json_string)
                stringa_mappata = base64.urlsafe_b64encode(compresso).decode('utf-8')
                
                # 2. Rileva dinamicamente l'indirizzo web dell'app per formare il link spettatori
                # Se l'app è su Streamlit Cloud userà l'URL corretto automaticamente
                url_base_app = "https://streamlit.app" # Sostituisci con l'URL finale se diverso
                if st.get_option("server.port") == 8501: # Se in locale su PC
                    url_base_app = "http://localhost:8501"
                    
                url_pubblico = f"{url_base_app}?match={stringa_mappata}"
                
                # 3. Genera il QR Code con il link interno nativo
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(url_pubblico)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                qr_buffer = io.BytesIO()
                img_qr.save(qr_buffer, format="PNG")
                qr_bytes = qr_buffer.getvalue()
                
                # 4. Compila il PDF definitivo inserendo il QR Code funzionante
                pdf_output = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_bytes)
                
                st.success("🎉 PDF Generato con successo in modo nativo!")
                st.write(f"📲 **URL codificato nel QR Code per il pubblico:** {url_pubblico}")
                
                st.download_button(
                    label="📥 Scarica Distinta di Gara Finale (PDF da Stampare)",
                    data=pdf_output,
                    file_name=f"distinta_{info_gara_corrette['data'].replace('/', '-')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Errore durante la creazione del file PDF: {e}")

