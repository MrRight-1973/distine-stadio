import streamlit as st
import os
import io
import re
from PIL import Image, ImageEnhance, ImageDraw
import qrcode
import pytesseract
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. CONFIGURAZIONE GRAFICA E VARIABILI DI STATO
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Scansione spaziale limitata rigorosamente alla fascia verticale dei numeri 1-20</p>", unsafe_allow_html=True)

if "dati_pronti" not in st.session_state:
    st.session_state.dati_pronti = False
if "casa_giocatori_input" not in st.session_state:
    st.session_state.casa_giocatori_input = [""] * 20
if "ospite_giocatori_input" not in st.session_state:
    st.session_state.ospite_giocatori_input = [""] * 20
if "squadra_casa_nome" not in st.session_state:
    st.session_state.squadra_casa_nome = "SQUADRA CASA"
if "squadra_ospite_nome" not in st.session_state:
    st.session_state.squadra_ospite_nome = "SQUADRA OSPITE"

# Configurazione dizionario italiano Tesseract per server Linux
os.environ["TESSDATA_PREFIX"] = os.getcwd()

# 2. PANNELLO DI CONFIGURAZIONE SIDEBAR
st.sidebar.header("⚙️ Configurazione Partita")
data_partita = st.sidebar.text_input("Data della partita", "28/09/2026")
campionato_info = st.sidebar.text_input("Campionato / Girone", "1° Categoria - Girone E")

st.sidebar.header("🏢 Pannello Sponsor (Max 5)")
sponsor_files = st.sidebar.file_uploader("Carica i loghi degli sponsor (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
if sponsor_files and len(sponsor_files) > 5:
    st.sidebar.error("Carica massimo 5 sponsor.")
    sponsor_files = sponsor_files[:5]

st.sidebar.header("⚖️ Terna Arbitrale")
nome_arbitro = st.sidebar.text_input("Arbitro (Sig.)", "")
assistente_1 = st.sidebar.text_input("Assistente 1", "")
assistente_2 = st.sidebar.text_input("Assistente 2", "")

# 3. INTERFACCIA DI CARICAMENTO FOTO
st.subheader("📸 Carica le FOTO delle distinte")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Foto Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Foto Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

# 4. MOTORE DI SCANSIONE AD ANCORAGGIO E RITAGLIO VERTICALE MIRATO
if foto_casa and foto_ospite:
    st.markdown("### 🔍 1. Analisi Geometrica e Allineamento sui Numeri di Riga")
    
    if st.button("🚀 AVVIA ESTRAZIONE PURA DALLE FOTO", use_container_width=True):
        with st.spinner("Isolamento della fascia verticale 1-20 ed estrazione nomi..."):
            
            def analizza_e_disegna_squadra(uploaded_file, etichetta_squadra):
                img_originale = Image.open(uploaded_file)
                img_disegno = img_originale.convert("RGB")
                draw = ImageDraw.Draw(img_disegno)
                
                larghezza_img, altezza_img = img_originale.size
                img_ocr = img_originale.convert('L')
                img_ocr = ImageEnhance.Contrast(img_ocr).enhance(3.0)
                
                dati_ocr = pytesseract.image_to_data(img_ocr, lang='ita', config='--psm 6', output_type=pytesseract.Output.DICT)
                n_elementi = len(dati_ocr['text'])
                
                x_numeri = []
                y_numeri = []
                mappa_y_numeri = {}
                
                # FASE 1: Trova i confini geometrici (Min Y e Max Y) della sola colonna 1-20
                for i in range(n_elementi):
                    testo = str(dati_ocr['text'][i]).strip()
                    if testo.isdigit():
                        num = int(testo)
                        if 1 <= num <= 20:
                            x_pos = dati_ocr['left'][i]
                            y_pos = dati_ocr['top'][i]
                            
                            # Filtro standard per escludere numeri sparsi nella metà destra del foglio
                            if x_pos < larghezza_img * 0.30: 
                                x_numeri.append(x_pos)
                                y_numeri.append(y_pos)
                                mappa_y_numeri[y_pos] = num

                # Definizione dei limiti della colonna numerica
                coordinata_x_ancora = int(sum(x_numeri) / len(x_numeri)) if x_numeri else int(larghezza_img * 0.08)
                
                # CORREZIONE FOCALIZZATA: L'area verticale inizia dal primo numero trovato e finisce all'ultimo
                limite_verticale_top = min(y_numeri) if y_numeri else int(altezza_img * 0.20)
                limite_verticale_bottom = max(y_numeri) + 40 if y_numeri else int(altezza_img * 0.85)
                
                # Calcolo dell'area orizzontale a destra del settore numerico
                col_nomi_left = coordinata_x_ancora + 25
                col_nomi_right = col_nomi_left + 450
                
                # Disegna il riquadro BLU focalizzato: parte dall'altezza dell'1 e si ferma all'altezza del 20
                draw.rectangle([col_nomi_left, limite_verticale_top, col_nomi_right, limite_verticale_bottom], outline="blue", width=6)
                
                # FASE 2: Raggruppamento parole filtrate per la sola area ritagliata
                giocatori_per_indice = {i: [] for i in range(1, 21)}
                tolleranza_y = 15
                
                for i in range(n_elementi):
                    testo_parola = str(dati_ocr['text'][i]).strip()
                    confidenza = int(dati_ocr['conf'][i])
                    
                    if confidenza < 35 or len(testo_parola) < 2 or testo_parola.isdigit():
                        continue
                        
                    x = dati_ocr['left'][i]
                    y = dati_ocr['top'][i]
                    w = dati_ocr['width'][i]
                    h = dati_ocr['height'][i]
                    
                    # Criterio di inclusione: deve essere dentro le X della colonna nomi E dentro le Y dei numeri 1-20
                    if (col_nomi_left <= x <= col_nomi_right) and (limite_verticale_top <= y <= limite_verticale_bottom):
                        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                        
                        for y_num, num_riga in mappa_y_numeri.items():
                            if abs(y_num - y) <= tolleranza_y:
                                if not any(z in testo_parola.upper() for z in ["COGNOME", "NOME", "ALLENATORE", "DISTINTA"]):
                                    giocatori_per_indice[num_riga].append(testo_parola)
                                break

                # FASE 3: Formattazione dei nomi estratti
                giocatori_finali = []
                for idx in range(1, 21):
                    stringa_nome = " ".join(giocatori_per_indice[idx]).strip()
                    stringa_nome = re.sub(r'[^a-zA-Z\sàèìòù🔍]', '', stringa_nome).strip()
                    
                    parole = stringa_nome.split()
                    if len(parole) >= 2:
                        cognome = parole[0].upper()
                        nome = " ".join(parole[1:]).title()
                        giocatori_finali.append(f"{cognome} {nome}")
                    elif len(parole) == 1:
                        giocatori_finali.append(parole[0].upper())
                    else:
                        giocatori_finali.append("")
                        
                return giocatori_finali, img_disegno

            g_casa, img_visto_casa = analizza_e_disegna_squadra(foto_casa, "CASA")
            g_ospite, img_visto_ospite = analizza_e_disegna_squadra(foto_ospite, "OSPITE")
            
            st.session_state.casa_giocatori_input = g_casa
            st.session_state.ospite_giocatori_input = g_ospite
            st.session_state.dati_pronti = True
            
            st.success("Estrazione focalizzata completata!")
            visto_col1, visto_col2 = st.columns(2)
            with visto_col1:
                st.image(img_visto_casa, caption="Area Nomi circoscritta alla fascia 1-20 (CASA)", use_container_width=True)
            with visto_col2:
                st.image(img_visto_ospite, caption="Area Nomi circoscritta alla fascia 1-20 (OSPITE)", use_container_width=True)
