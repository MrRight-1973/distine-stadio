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
st.markdown("<p style='text-align: center; color: #4A5568;'>Scansione spaziale basata su colonna numerica progressiva 1-20</p>", unsafe_allow_html=True)

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

# 4. MOTORE DI SCANSIONE AD ANCORAGGIO NUMERICO
if foto_casa and foto_ospite:
    st.markdown("### 🔍 1. Analisi Geometrica e Allineamento sui Numeri di Riga")
    
    if st.button("🚀 AVVIA ESTRAZIONE PURA DALLE FOTO", use_container_width=True):
        with st.spinner("Allineamento sui numeri guida 1-20 ed estrazione anagrafica..."):
            
            def analizza_e_disegna_squadra(uploaded_file, etichetta_squadra):
                img_originale = Image.open(uploaded_file)
                img_disegno = img_originale.convert("RGB")
                draw = ImageDraw.Draw(img_disegno)
                
                larghezza_img, altezza_img = img_originale.size
                img_ocr = img_originale.convert('L')
                img_ocr = ImageEnhance.Contrast(img_ocr).enhance(3.0)
                
                # Usiamo image_to_data per trovare la posizione di ogni singola parola/numero
                dati_ocr = pytesseract.image_to_data(img_ocr, lang='ita', config='--psm 6', output_type=pytesseract.Output.DICT)
                n_elementi = len(dati_ocr['text'])
                
                # FASE 1: Individuazione della coordinata X media dei numeri progressivi da 1 a 20
                x_numeri = []
                mappa_y_numeri = {} # Associa il numero letto alla sua altezza Y
                
                for i in range(n_elementi):
                    testo = str(dati_ocr['text'][i]).strip()
                    # Controlla se la parola è un numero puro compreso tra 1 e 20
                    if testo.isdigit():
                        num = int(testo)
                        if 1 <= num <= 20:
                            x_pos = dati_ocr['left'][i]
                            y_pos = dati_ocr['top'][i]
                            # Filtro per escludere numeri sparsi a destra (es. anni o tessere)
                            if x_pos < larghezza_img * 0.30: 
                                x_numeri.append(x_pos)
                                mappa_y_numeri[y_pos] = num

                # Determina l'asse X della colonna numerica
                if x_numeri:
                    coordinata_x_ancora = int(sum(x_numeri) / len(x_numeri))
                else:
                    # Fallback geometrico se non legge i numeri impressi
                    coordinata_x_ancora = int(larghezza_img * 0.08)
                
                # Calcola l'area della colonna BLU dei Nomi partendo subito a destra dell'ancora numerica
                col_nomi_left = coordinata_x_ancora + 25   # Salta lo spazio del numero e del trattino
                col_nomi_right = col_nomi_left + 450       # Larghezza utile per contenere COGNOME Nome
                
                # Disegna l'area BLU focalizzata sui nomi
                draw.rectangle([col_nomi_left, 0, col_nomi_right, altezza_img], outline="blue", width=6)
                
                # FASE 2: Raggruppamento dei frammenti di testo allineati sulle Y dei numeri guida
                giocatori_per_indice = {i: [] for i in range(1, 21)}
                tolleranza_y = 15 # Pixel di tolleranza per scritte leggermente ondulate
                
                for i in range(n_elementi):
                    testo_parola = str(dati_ocr['text'][i]).strip()
                    confidenza = int(dati_ocr['conf'][i])
                    
                    if confidenza < 35 or len(testo_parola) < 2 or testo_parola.isdigit():
                        continue
                        
                    x = dati_ocr['left'][i]
                    y = dati_ocr['top'][i]
                    w = dati_ocr['width'][i]
                    h = dati_ocr['height'][i]
                    
                    # Se la parola cade dentro l'area BLU dei Nomi
                    if col_nomi_left <= x <= col_nomi_right:
                        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                        
                        # Associa la parola alla riga del rispettivo numero da 1 a 20
                        for y_num, num_riga in mappa_y_numeri.items():
                            if abs(y_num - y) <= tolleranza_y:
                                if not any(z in testo_parola.upper() for z in ["COGNOME", "NOME", "ALLENATORE", "DISTINTA"]):
                                    giocatori_per_indice[num_riga].append(testo_parola)
                                break

                # FASE 3: Formattazione ordinata dei 20 slot richiesti
                giocatori_finali = []
                for idx in range(1, 21):
                    stringa_nome = " ".join(giocatori_per_indice[idx]).strip()
                    # Rimuove caratteri speciali spuri o simboli rimasti dall'OCR
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
                st.image(img_visto_casa, caption="Area Nomi agganciata alla sequenza 1-20 (CASA)", use_container_width=True)
            with visto_col2:
                st.image(img_visto_ospite, caption="Area Nomi agganciata alla sequenza 1-20 (OSPITE)", use_container_width=True)
