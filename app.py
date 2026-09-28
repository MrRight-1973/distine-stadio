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
st.markdown("<p style='text-align: center; color: #4A5568;'>Scansione spaziale delle colonne, pannello di verifica e stampa A4 con QR Code</p>", unsafe_allow_html=True)

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

# 3. INTERFACCIA DI CARICAMENTO FOTO UPLODER
st.subheader("📸 Carica le FOTO delle distinte")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Foto Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Foto Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

# 4. MOTORE DI SCANSIONE ESTRATTORE GEOMETRICO
if foto_casa and foto_ospite:
    st.markdown("### 🔍 1. Analisi e verifica geometrica delle colonne")
    
    if st.button("🚀 AVVIA ESTRAZIONE PURA DALLE FOTO", use_container_width=True):
        with st.spinner("Il motore spaziale sta tracciando le coordinate X/Y delle colonne..."):
            
            def analizza_e_disegna_squadra(uploaded_file, etichetta_squadra):
                img_originale = Image.open(uploaded_file)
                img_disegno = img_originale.convert("RGB")
                draw = ImageDraw.Draw(img_disegno)
                
                larghezza_img, altezza_img = img_originale.size
                img_ocr = img_originale.convert('L')
                img_ocr = ImageEnhance.Contrast(img_ocr).enhance(3.0)
                
                dati_ocr = pytesseract.image_to_data(img_ocr, lang='ita', config='--psm 6', output_type=pytesseract.Output.DICT)
                
                col_nomi_left = None
                col_nomi_right = None
                col_nascita_left = None
                col_nascita_right = None
                n_elementi = len(dati_ocr['text'])
                
                for i in range(n_elementi):
                    testo = str(dati_ocr['text'][i]).upper().strip()
                    if "COGNOME" in testo or "NOME" in testo:
                        if col_nomi_left is None:
                            col_nomi_left = dati_ocr['left'][i] - 20
                            col_nomi_right = col_nomi_left + 450
                    if "NASCITA" in testo or "DATA" in testo or "NASC" in testo:
                        if col_nascita_left is None:
                            col_nascita_left = dati_ocr['left'][i] - 15
                            col_nascita_right = col_nascita_left + 180

                if col_nomi_left is None:
                    col_nomi_left, col_nomi_right = int(larghezza_img * 0.15), int(larghezza_img * 0.55)
                if col_nascita_left is None:
                    col_nascita_left, col_nascita_right = int(larghezza_img * 0.58), int(larghezza_img * 0.85)

                # Disegno dei rettangoli di contenimento colonne
                draw.rectangle([col_nomi_left, 0, col_nomi_right, altezza_img], outline="blue", width=6)
                draw.rectangle([col_nascita_left, 0, col_nascita_right, altezza_img], outline="green", width=6)

                righe_mappate = {}
                tolleranza_y = 12 
                
                for i in range(n_elementi):
                    testo_parola = str(dati_ocr['text'][i]).strip()
                    confidenza = int(dati_ocr['conf'][i])
                    if confidenza < 35 or len(testo_parola) < 2:
                        continue
                        
                    x = dati_ocr['left'][i]
                    y = dati_ocr['top'][i]
                    w = dati_ocr['width'][i]
                    h = dati_ocr['height'][i]
                    
                    if col_nomi_left <= x <= col_nomi_right or col_nascita_left <= x <= col_nascita_right:
                        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                        
                        riga_y = None
                        for y_chiave in righe_mappate.keys():
                            if abs(y_chiave - y) <= tolleranza_y:
                                riga_y = y_chiave
                                break
                        if riga_y is None:
                            riga_y = y
                            righe_mappate[riga_y] = {"nomi": [], "nascita": []}
                            
                        if col_nomi_left <= x <= col_nomi_right:
                            if not any(z in testo_parola.upper() for z in ["COGNOME", "NOME", "ALLENATORE"]):
                                righe_mappate[riga_y]["nomi"].append(testo_parola)
                        elif col_nascita_left <= x <= col_nascita_right:
                            if not any(z in testo_parola.upper() for z in ["NASCITA", "DATA", "ANNO"]):
                                righe_mappate[riga_y]["nascita"].append(testo_parola)

                giocatori_finali = []
                for y in sorted(righe_mappate.keys()):
                    stringa_nome = " ".join(righe_mappate[y]["nomi"]).strip()
                    stringa_nascita = "".join(righe_mappate[y]["nascita"]).strip()
                    if not stringa_nome or len(re.sub(r'[^a-zA-Z]', '', stringa_nome)) < 3:
                        continue
                    
                    match_anno = re.search(r'\b(\d{2,4})\b', stringa_nascita)
                    anno_pulito = f"'{match_anno.group(1)[-2:]}" if match_anno else ""
                    
                    parole = stringa_nome.split()
                    if len(parole) >= 2:
                        cognome = parole[0].upper()
                        nome = " ".join(parole[1:]).title()
                        riga_giocatore = f"{cognome} {nome}"
                    else:
                        riga_giocatore = parole[0].upper() if parole else ""
                        
                    if anno_pulito and riga_giocatore:
                        riga_giocatore += f" ({anno_pulito})"
                    if riga_giocatore:
                        giocatori_finali.append(riga_giocatore)

                giocatori_finali = list(dict.fromkeys(giocatori_finali))
                while len(giocatori_finali) < 20:
                    giocatori_finali.append("")
                return giocatori_finali[:20], img_disegno

            g_casa, img_visto_casa = analizza_e_disegna_squadra(foto_casa, "CASA")
            g_ospite, img_visto_ospite = analizza_e_disegna_squadra(foto_ospite, "OSPITE")
            
            st.session_state.casa_giocatori_input = g_casa
            st.session_state.ospite_giocatori_input = g_ospite
            st.session_state.dati_pronti = True
            
            st.success("Estrazione completata!")
            visto_col1, visto_col2 = st.columns(2)
            with visto_col1:
                st.image(img_visto_casa, caption="Allineamento geometrico CASA (Blu/Verde)", use_container_width=True)
            with visto_col2:
                st.image(img_visto_ospite, caption="Allineamento geometrico OSPITE (Blu/Verde)", use_container_width=True)

if st.session_state.dati_pronti:
    st.markdown("---")
    
    if st.button("🔄 INVERTI SQUADRA CASA / OSPITE", use_container_width=True):
        st.session_state.squadra_casa_nome, st.session_state.squadra_ospite_nome = st.session_state.squadra_ospite_nome, st.session_state.squadra_casa_nome
        st.session_state.casa_giocatori_input, st.session_state.ospite_giocatori_input = st.session_state.ospite_giocatori_input, st.session_state.casa_giocatori_input
        st.rerun()

    st.warning("📝 **Pannello di Controllo Segreteria:** Dati estratti geometricamente. Correggi eventuali piccoli refusi prima di stampare.")
    
    edit_col1, edit_col2 = st.columns(2)
    lista_casa_corretta = []
    lista_ospite_corretta = []
    
    with edit_col1:
        st.subheader("Modifica SQUADRA CASA")
        nome_squadra_casa = st.text_input("Nome Società Ospitante (CASA)", st.session_state.squadra_casa_nome)
        st.markdown("**Giocatori (Progressione automatica):**")
        for idx, player in enumerate(st.session_state.casa_giocatori_input):
            p_val = st.text_input(f"Casa - N. {idx+1}", value=player, key=f"c_p_{idx}")
            lista_casa_corretta.append(p_val)
            
    with edit_col2:
        st.subheader("Modifica SQUADRA OSPITE")
        nome_squadra_ospite = st.text_input("Nome Società Ospite (OSPITE)", st.session_state.squadra_ospite_nome)
        st.markdown("**Giocatori (Progressione automatica):**")
        for idx, player in enumerate(st.session_state.ospite_giocatori_input):
            p_val = st.text_input(f"Ospite - N. {idx+1}", value=player, key=f"o_p_{idx}")
            lista_ospite_corretta.append(p_val)

    def genera_pdf_distinte():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor('#1A365D'))
        subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor('#4A5568'))
        th_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=11, leading=14, bold=True, textColor=colors.white, alignment=1)
        td_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=9, leading=12)
        
        story.append(Paragraph("⚽ DISTINTA UFFICIALE DI GARA", title_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Campionato:</b> {campionato_info} | <b>Data:</b> {data_partita}", subtitle_style))
        story.append(Spacer(1, 15))
        
        match_title_style = ParagraphStyle('MatchTitle', parent=styles['Heading2'], fontSize=14, leading=18, alignment=1, bold=True)
        data_match = [[Paragraph(f"{nome_squadra_casa} vs {nome_squadra_ospite}", match_title_style)]]
        t_match = Table(data_match, colWidths=[535])
        t_match.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
            ('PADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor('#1A365D'))
        ]))
        story.append(t_match)
        story.append(Spacer(1, 15))
        
        # Generazione QR Code unico del match per l'ingresso stadio
        qr_data = f"Match: {nome_squadra_casa} vs {nome_squadra_ospite}\nData: {data_partita}\nCamp: {campionato_info}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = io.BytesIO()
        img_qr.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        rl_qr_img = RLImage(qr_buffer, width=70, height=70)
        
        arbitri_testo = f"<b>Arbitro:</b> {nome_arbitro}<br/><b>Assistente 1:</b> {assistente_1}<br/><b>Assistente 2:</b> {assistente_2}"
        data_info = [[Paragraph(arbitri_testo, td_style), rl_qr_img]]
        t_info = Table(data_info, colWidths=[450, 85])
        t_info.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('PADDING', (0,0), (-1,-1), 5)
        ]))
        story.append(t_info)
        story.append(Spacer(1, 15))
        
        corpo_tabella = [[Paragraph(nome_squadra_casa, th_style), Paragraph(nome_squadra_ospite, th_style)]]
        
        for i in range(20):
            p_casa = lista_casa_corretta[i] if i < len(lista_casa_corretta) else ""
            p_ospite = lista_ospite_corretta[i] if i < len(lista_ospite_corretta) else ""
            txt_c = f"<b>{i+1}.</b> {p_casa}" if p_casa else ""
            txt_o = f"<b>{i+1}.</b> {p_ospite}" if p_ospite else ""
            corpo_tabella.append([Paragraph(txt_c, td_style), Paragraph(txt_o, td_style)])
            
        t_giocatori = Table(corpo_tabella, colWidths=[267, 268])
        t_giocatori.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#1A365D')),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor('#C53030')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F7FAFC')])
        ]))
        story.append(t_giocatori)
        story.append(Spacer(1, 20))
        
        if sponsor_files:
            story.append(Paragraph("<b>SPONSOR UFFICIALI</b>", ParagraphStyle('SponsTitle', parent=styles['Normal'], fontSize=9, bold=True, textColor=colors.HexColor('#718096'), alignment=1)))
            story.append(Spacer(1, 5))
            
            sponsor_images = []
            for sp_file in sponsor_files:
                try:
                    sp_file.seek(0)
                    sp_img = RLImage(io.BytesIO(sp_file.read()), width=60, height=30)
                    sponsor_images.append(sp_img)
                except:
                    pass
            
            if sponsor_images:
                while len(sponsor_images) < 5:
                    sponsor_images.append("")
                t_sponsor = Table([sponsor_images], colWidths=[107]*5)
                t_sponsor.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
                ]))
                story.append(t_sponsor)
                
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    st.markdown("---")
    st.subheader("🖨️ Stampa e Validazione")
    pdf_data = genera_pdf_distinte()
    
    st.download_button(
        label="📥 SCARICA DISTINTA UFFICIALE IN PDF (A4)",
        data=pdf_data,
        file_name=f"distinta_{data_partita.replace('/', '-')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
