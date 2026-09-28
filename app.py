import streamlit as st
import io
import qrcode
import requests
import base64
import pandas as pd
from estrattore import analizza_distinta, genera_pdf, pulisci_testo

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

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

    # --- GENERAZIONE PDF FINALE PER SPETTATORI (TMPFILES.ORG) ---
    st.markdown("---")
    if st.button("⚡ Fase 3: Conferma e Genera PDF A4 con QR Code Pubblico", type="primary"):
        with st.spinner("Generazione del foglio di gara e caricamento cloud per gli spettatori..."):
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
                
                # 1. Genera una prima bozza del PDF (senza QR code momentaneamente)
                pdf_bozza = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_code_bytes=None)
                
                # 2. Carica il PDF online tramite filebin.net (Server ultra-stabile e simultaneo)
                url_pubblico = "https://google.com" # Fallback globale
                caricato_con_successo = False
                
                try:
                    # Filebin richiede di definire un "bin" (un contenitore) univoco, creiamolo con la data e un codice casuale
                    import random
                    id_partita = f"distinta_{info_gara_corrette['data'].replace('/', '_')}_{random.randint(1000, 9999)}".lower()
                    nome_file = f"distinta_{info_gara_corrette['data'].replace('/', '_')}.pdf"
                    
                    # URL di upload diretto per il filebin
                    upload_url = f"https://filebin.net{id_partita}/{nome_file}"
                    
                    # Inviamo i byte crudi del PDF tramite richiesta PUT (standard per filebin)
                    headers = {"Content-Type": "application/pdf"}
                    response_upload = requests.put(upload_url, data=pdf_bozza, headers=headers, timeout=10)
                    
                    if response_upload.status_code in:
                        # L'URL di download diretto per gli spettatori sarà questo:
                        url_pubblico = f"https://filebin.net{id_partita}/{nome_file}"
                        caricato_con_successo = True
                    else:
                        st.warning(f"Il server di hosting ha risposto con codice {response_upload.status_code}. Tento fallback rapido...")
                        # Fallback integrato su ix.io (senza chiamare .seek())
                        payload_ix = {'f:1': pdf_bozza}
                        response_ix = requests.post("http://ix.io", data=payload_ix, timeout=8)
                        if response_ix.status_code == 200:
                            url_pubblico = response_ix.text.strip()
                            caricato_con_successo = True
                            
                except Exception as e_upload:
                    st.warning(f"Errore durante il caricamento cloud: {e_upload}. Genero comunque il PDF locale.")

                # 3. Genera il QR Code contenente l'URL risultante
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(url_pubblico)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                qr_buffer = io.BytesIO()
                img_qr.save(qr_buffer, format="PNG")
                qr_bytes = qr_buffer.getvalue()
                
                # 4. Rigenera il PDF inserendo il QR Code definitivo
                pdf_output = genera_pdf(squadra_casa_corretta, squadra_ospite_corretta, info_gara_corrette, qr_bytes)
                
                if caricato_con_successo:
                    st.success("🎉 PDF Generato e caricato online! Il QR Code è attivo per tutto il pubblico (durata 24h).")
                    st.write(f"🔗 **Link diretto spettatori:** {url_pubblico}")
                else:
                    st.error("⚠️ PDF generato solo in locale. Il QR code sul foglio non sarà raggiungibile dagli smartphone degli spettatori.")
                
                st.download_button(
                    label="📥 Scarica Distinta di Gara Finale (PDF da Stampare)",
                    data=pdf_output,
                    file_name=f"distinta_{info_gara_corrette['data'].replace('/', '-')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Errore generico durante la creazione del file PDF: {e}")

