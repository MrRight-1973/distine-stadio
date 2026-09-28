import streamlit as st
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import re
from PIL import Image, ImageEnhance
import qrcode
import pytesseract

# Configurazione grafica della pagina web
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Scansione FOTO totale, pannello di correzione e stampa A4</p>", unsafe_allow_html=True)

# Uso dello Session State di Streamlit per memorizzare le modifiche della segreteria
if "dati_pronti" not in st.session_state:
    st.session_state.dati_pronti = False
if "casa_giocatori_input" not in st.session_state:
    st.session_state.casa_giocatori_input = []
if "ospite_giocatori_input" not in st.session_state:
    st.session_state.ospite_giocatori_input = []
if "casa_all_input" not in st.session_state:
    st.session_state.casa_all_input = ""
if "ospite_all_input" not in st.session_state:
    st.session_state.ospite_all_input = ""
if "squadra_casa_nome" not in st.session_state:
    st.session_state.squadra_casa_nome = "SQUADRA CASA"
if "squadra_ospite_nome" not in st.session_state:
    st.session_state.squadra_ospite_nome = "SQUADRA OSPITE"

# 1. SIDEBAR: CONFIGURAZIONE
st.sidebar.header("⚙️ Configurazione Partita")
data_partita = st.sidebar.text_input("Data della partita", "28/09/2026")
campionato_info = st.sidebar.text_input("Campionato / Girone", "1° Categoria - Girone E")

st.sidebar.header("🏢 Pannello Sponsor (Max 5)")
sponsor_files = st.sidebar.file_uploader("Carica i loghi degli sponsor (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
if len(sponsor_files) > 5:
    st.sidebar.error("Carica massimo 5 sponsor.")
    sponsor_files = sponsor_files[:5]

st.sidebar.header("⚖️ Terna Arbitrale")
nome_arbitro = st.sidebar.text_input("Arbitro (Sig.)", "")
assistente_1 = st.sidebar.text_input("Assistente 1", "")
assistente_2 = st.sidebar.text_input("Assistente 2", "")

st.subheader("📸 Carica le FOTO delle distinte")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Foto Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Foto Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

def formatta_riga_ocr_inclusiva(testo_grezzo):
    """Estrae e protegge qualsiasi blocco di testo utile letto sulla foto cartacea"""
    testo_grezzo = testo_grezzo.strip()
    if len(testo_grezzo) < 3:
        return ""
        
    # Isola l'anno di nascita (2 cifre consecutive nell'intervallo tipico dei calciatori)
    match_anno = re.search(r'\b(19|20)?(\d{2})\b', testo_grezzo)
    anno = f"'{match_anno.group(2)}" if match_anno else ""
    
    # Isola i ruoli di Capitano e Vice prima di pulire i simboli
    ruolo = ""
    if "(C)" in testo_grezzo.upper() or " C " in testo_grezzo.upper() or "  C  " in testo_grezzo.upper(): 
        ruolo = " (C)"
    elif any(x in testo_grezzo.upper() for x in ["(VC)", "(V)", " VC ", " V "]): 
        ruolo = " (VC)"
        
    # Rimuove solo i lunghi numeri di tessera o codici a barre della FIGC
    testo_puro = re.sub(r'\b\d{4,9}\b', '', testo_grezzo)
    # Rimuove la vecchia numerazione iniziale della riga
    testo_puro = re.sub(r'^\d+[\s\.\-]*', '', testo_puro).strip()
    
    # Pulisce dai caratteri speciali ma tiene intatte tutte le lettere dell'alfabeto
    testo_puro = re.sub(r'[^a-zA-Z\s]', '', testo_puro).strip()
    testo_puro = testo_puro.replace("C", "").replace("VC", "").replace("V", "").strip()
    
    parole = testo_puro.split()
    if len(parole) >= 1:
        cognome = parole[0].upper()
        nome = " ".join(parole[1:]).title() if len(parole) > 1 else ""
        
        risultato_anagrafica = f"{cognome} {nome}".strip()
        if risultato_anagrafica:
            res_finale = f"{risultato_anagrafica}{ruolo}"
            return f"{res_finale} ({anno})" if anno else res_finale
            
    return ""

def esegui_ocr_foto_inclusivo(uploaded_file):
    """Scansiona l'immagine ed estrae ogni riga di testo utile senza scartare nulla"""
    giocatori = []
    all_nome = "Non rilevato"
    squadra_nome = "SQUADRA RILEVATA"
    try:
        img = Image.open(uploaded_file)
        # Ottimizzazione dell'immagine per Tesseract (aumento contrasto per fogli in ombra)
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.0)
        
        testo = pytesseract.image_to_string(img, lang='ita')
        righe = testo.split('\n')
        
        for riga in righe:
            riga_clean = riga.strip()
            if len(riga_clean) < 3 or any(x in riga_clean.upper() for x in ["FEDERAZIONE", "CAMPIONATO", "COMITATO", "SOCIETA"]):
                continue
                
            if "ALLENATORE" in riga_clean.upper() or "ALL." in riga_clean.upper():
                all_nome = re.sub(r'[^a-zA-Z\s]', '', riga_clean).replace("ALLENATORE", "").replace("All", "").strip().upper()
                continue
                
            if ("ASD" in riga_clean.upper() or "AZZURRA" in riga_clean.upper() or "PETTORAZZA" in riga_clean.upper()) and squadra_nome == "SQUADRA RILEVATA":
                squadra_nome = riga_clean.upper().strip()
                continue
                
            testo_formattato = formatta_riga_ocr_inclusiva(riga_clean)
            if testo_formattato and not any(x in testo_formattato.upper() for x in ["DIRIGENTE", "MEDICO", "MASSAGGIATORE", "TESSERA", "ASSISTENTE"]):
                if testo_formattato not in giocatori:
                    giocatori.append(testo_formattato)
    except:
        pass
        
    while len(giocatori) < 20:
        giocatori.append("")
    # RISOLTO: Sostituito 'jugadores' con 'giocatori'
    return giocatori[:20], all_nome.title(), squadra_nome

if foto_casa and foto_ospite:
    if st.button("🔍 1. ESTRAI E RIVEDERE I DATI DALLE FOTO", use_container_width=True):
        with st.spinner("Il motore Tesseract sta eseguendo la mappatura completa dei pixel testuali..."):
            g_casa, a_casa, name_casa = esegui_ocr_foto_inclusivo(foto_casa)
            g_ospite, a_ospite, name_ospite = esegui_ocr_foto_inclusivo(foto_ospite)
            
            # Scambio automatico se la segreteria inverte l'ordine dei moduli cartacei
            if "pettorazza" in foto_casa.name.lower() or "ospite" in foto_casa.name.lower():
                st.session_state.casa_giocatori_input = g_ospite
                st.session_state.casa_all_input = a_ospite
                st.session_state.squadra_casa_nome = name_ospite
                st.session_state.ospite_giocatori_input = g_casa
                st.session_state.ospite_all_input = a_casa
                st.session_state.squadra_ospite_nome = name_casa
            else:
                st.session_state.casa_giocatori_input = g_casa
                st.session_state.casa_all_input = a_casa
                st.session_state.squadra_casa_nome = name_casa
                st.session_state.ospite_giocatori_input = g_ospite
                st.session_state.ospite_all_input = a_ospite
                st.session_state.squadra_ospite_nome = name_ospite
                
            st.session_state.dati_pronti = True

if st.session_state.dati_pronti:
    st.markdown("---")
    st.warning("📝 **Pannello di Controllo Segreteria:** Dati estratti dalle immagini. Correggi eventuali lettere sfocate direttamente qui sotto prima di stampare.")
    edit_col1, edit_col2 = st.columns(2)
    lista_casa_corretta, lista_ospite_corretta = [], []
    
    with edit_col1:
        st.subheader("Società Ospitante (CASA)")
        nome_squadra_casa = st.text_input("Nome Club Casa", st.session_state.squadra_casa_nome)
        c_all_edit = st.text_input("Allenatore Casa", st.session_state.casa_all_input)
        st.markdown("**Giocatori (Progressione 1-20):**")
        for idx, player in enumerate(st.session_state.casa_giocatori_input):
            valore_corretto = st.text_input(f"Casa - Maglia {idx+1}", value=player, key=f"c_{idx}")
            lista_casa_corretta.append(f"{idx+1}. {valore_corretto}")
            
    with edit_col2:
        st.subheader("Società Ospite")
        nome_squadra_ospite = st.text_input("Nome Club Ospite", st.session_state.squadra_ospite_nome)
        o_all_edit = st.text_input("Allenatore Ospite", st.session_state.ospite_all_input)
        st.markdown("**Giocatori (Progressione 1-20):**")
        for idx, player in enumerate(st.session_state.ospite_giocatori_input):
            valore_corretto = st.text_input(f"Ospite - Maglia {idx+1}", value=player, key=f"o_{idx}")
            lista_ospite_corretta.append(f"{idx+1}. {valore_corretto}")

    st.markdown("---")
    if st.button("🚀 2. GENERA PDF DEFINITIVO PER IL PUBBLICO", use_container_width=True):
        with st.spinner("Compilazione foglio A4 con QR Code e Sponsor..."):
            app_url = st.build_info.get("origin", "https://streamlit.io") if hasattr(st, "build_info") else "https://streamlit.io"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(app_url)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            img_qr.save("temp_pdf_qr.png")
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=20, bottomMargin=20)
            story, styles = [], getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=2)
            sub_style = ParagraphStyle('S', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=10)
            team_title_style = ParagraphStyle('TT', fontSize=11, leading=14, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            player_style = ParagraphStyle('P', fontSize=8.2, leading=10.5, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=8.2, leading=10.5, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=10)
            qr_text_style = ParagraphStyle('QT', fontSize=7.5, leading=10, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold")

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            box_casa = [Paragraph(nome_squadra_casa.upper(), team_title_style), Spacer(1, 2)]
            for g in lista_casa_corretta: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 4))
            box_casa.append(Paragraph(f"<b>All.</b> {c_all_edit}", staff_style))
            
            box_ospite = [Paragraph(nome_squadra_ospite.upper(), team_title_style), Spacer(1, 2)]
            for g in lista_ospite_corretta: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 4))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_all_edit}", staff_style))
            
            grid = Table([[box_casa, box_ospite]], colWidths=[260, 260])
            grid.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('RIGHTPADDING', (0,0), (0,0), 15), ('LEFTPADDING', (1,0), (1,0), 15)]))
            story.append(grid)
            story.append(Spacer(1, 8))
            
            if sponsor_files:
                blocchi_sponsor = []
                num_sponsor = min(len(sponsor_files), 5)
                width_singolo = int(480 / num_sponsor) - 10
                for idx, s_file in enumerate(sponsor_files[:5]):
                    try:
                        img = Image.open(s_file).convert("RGBA")
                        alpha = img.split()
                        alpha = ImageEnhance.Brightness(alpha).enhance(0.25)
                        img.putalpha(alpha)
                        temp_path = f"temp_sponsor_{idx}.png"
                        img.save(temp_path)
                        blocchi_sponsor.append(RLImage(temp_path, width=width_singolo, height=35, kind='proportional'))
                    except: pass
                if blocchi_sponsor:
                    tabella_sponsor = Table([blocchi_sponsor], colWidths=[width_singolo+10]*len(blocchi_sponsor))
                    tabella_sponsor.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
                    story.append(tabella_sponsor)
            
            story.append(Paragraph("INQUADRA IL CODICE PER SCARICARE LE FORMAZIONI SUL TELEFONO", qr_text_style))
            story.append(Spacer(1, 2))
            story.append(RLImage("temp_pdf_qr.png", width=65, height=65))
            
            def draw_background_fallback(canvas, doc):
                if not sponsor_files:
                    canvas.saveState()
                    canvas.setFont('Helvetica-Bold', 40)
                    canvas.setFillColor(colors.HexColor("#F2F4F7"))
                    canvas.translate(297.5, 420.5) 
                    canvas.rotate(35)
                    canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
                    canvas.restoreState()

            doc.build(story, onFirstPage=draw_background_fallback, onLaterPages=draw_background_fallback)
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            st.success("✅ Distinta da foto generata con successo!")
            st.download_button(label="📥 Scarica PDF Distinta Verificata", data=pdf_bytes, file_name=f"Distinta_Stadio_{data_partita.replace('/', '-')}.pdf", mime="application/pdf", use_container_width=True)
