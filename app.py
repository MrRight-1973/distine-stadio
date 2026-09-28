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
st.markdown("<p style='text-align: center; color: #4A5568;'>Scansione FOTO reale ad alta precisione, pannello di controllo e stampa A4</p>", unsafe_allow_html=True)

# Uso dello Session State di Streamlit per memorizzare le modifiche della segreteria
if "dati_pronti" not in st.session_state:
    st.session_state.dati_pronti = False
if "casa_giocatori_input" not in st.session_state:
    st.session_state.casa_giocatori_input = [""] * 20
if "ospite_giocatori_input" not in st.session_state:
    st.session_state.ospite_giocatori_input = [""] * 20
if "casa_all_input" not in st.session_state:
    st.session_state.casa_all_input = ""
if "ospite_all_input" not in st.session_state:
    st.session_state.ospite_all_input = ""
if "squadra_casa_nome" not in st.session_state:
    st.session_state.squadra_casa_nome = "SQUADRA CASA"
if "squadra_ospite_nome" not in st.session_state:
    st.session_state.squadra_ospite_nome = "SQUADRA OSPITE"

# CONFIGURAZIONE PUNTAZIONE LOCALE DIZIONARIO ITALIANO
os.environ["TESSDATA_PREFIX"] = os.getcwd()

# 1. SIDEBAR: CONFIGURAZIONE
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

st.subheader("📸 Carica le FOTO delle distinte")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Foto Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Foto Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

def formatta_riga_giocatore_reale(testo_grezzo):
    """Estrattore semantico: separa i blocchi alfabetici ignorando codici numerici e stringhe orizzontali orfane"""
    # 1. Trova l'anno di nascita (cifra di 2 o 4 cifre isolata)
    match_anno = re.search(r'\b(19|20)?(\d{2})\b', testo_grezzo)
    anno = f"'{match_anno.group(2)}" if match_anno else ""
    
    # 2. Rileva i ruoli speciali
    ruolo = ""
    if any(x in testo_grezzo.upper() for x in ["(C)", " C ", "CAPITANO"]): ruolo = " (C)"
    elif any(x in testo_grezzo.upper() for x in ["(VC)", "(V)", " VC ", " VICE "]): ruolo = " (VC)"
    
    # 3. Pulisce la stringa mantenendo solo lettere e spazi
    pulito = re.sub(r'[^a-zA-Z\sàèìòù🔍]', ' ', testo_grezzo)
    parole = [p for p in pulito.split() if len(p) > 1] # Scarta lettere singole orfane dovute a errori OCR
    
    # 4. Strategia di accoppiamento Cognome (Maiuscolo) e Nome (Minuscolo/Misto)
    cognomi = []
    nomi = []
    
    for p in parole:
        # Se la parola contiene parole chiave strutturali dei moduli, la saltiamo
        if p.upper() in ["DIRIGENTE", "MEDICO", "TESSERA", "ASSISTENTE", "ALLENATORE", "ALL", "ASD", "FC", "AC"]:
            continue
        # Se è scritta interamente in MAIUSCOLO (e ha più di 2 lettere) è probabilmente un cognome
        if p.isupper() and len(p) >= 2:
            cognomi.append(p)
        else:
            nomi.append(p.title())
            
    # Se non ha trovato una netta separazione maiuscole/minuscole, usa l'ordine standard dei blocchi di testo
    if not cognomi and len(parole) >= 2:
        cognomi.append(parole[0].upper())
        nomi = [p.title() for p in parole[1:]]
        
    if cognomi:
        cognome_finale = " ".join(cognomi)
        nome_finale = " ".join(nomi) if nomi else ""
        res = f"{cognome_finale} {nome_finale}".strip()
        
        # Aggiunge i metadati trovati
        res = f"{res}{ruolo}"
        if anno:
            res = f"{res} ({anno})"
        return res
        
    return ""

def esegui_ocr_foto_reale(uploaded_file):
    """
    Isola geometricamente le colonne 'Nome e Cognome' e 'Data di nascita'
    abbinando i dati riga per riga tramite coordinate pixel.
    """
    giocatori_estratti = []
    squadra_nome = "SQUADRA RILEVATA"
    all_nome = ""
    
    try:
        img = Image.open(uploaded_file).convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.5)
        
        # Estraiamo i dati completi di coordinate (x, y, larghezza, altezza, testo)
        dati_ocr = pytesseract.image_to_data(img, lang='ita', output_type=pytesseract.Output.DICT)
        
        col_nomi_left = None
        col_nomi_right = None
        col_nascita_left = None
        col_nascita_right = None
        
        n_elementi = len(dati_ocr['text'])
        
        # FASE 1: Individuazione geometrica delle colonne di interesse
        for i in range(n_elementi):
            testo = str(dati_ocr['text'][i]).upper().strip()
            
            # Cerca l'intestazione della colonna Nomi
            if "COGNOME" in testo or "NOME" in testo:
                col_nomi_left = dati_ocr['left'][i] - 20  # Margine di tolleranza a sinistra
                col_nomi_right = col_nomi_left + 400     # Estensione stimata della colonna nomi
                
            # Cerca l'intestazione della colonna Data di Nascita
            if "NASCITA" in testo or "DATA" in testo or "NASC" in testo:
                col_nascita_left = dati_ocr['left'][i] - 15
                col_nascita_right = col_nascita_left + 150
                
            # Cerca il nome della squadra (es. ASD, FC) nelle righe alte
            if any(x in testo for x in ["ASD", "F.C.", "AC", "CLUB"]) and dati_ocr['top'][i] < 300:
                squadra_nome = str(dati_ocr['text'][i]).upper()
        
        # Se le colonne non vengono rilevate via testo, applichiamo dei fallback proporzionali standard
        img_width, _ = img.size
        if not col_nomi_left:
            col_nomi_left, col_nomi_right = int(img_width * 0.15), int(img_width * 0.55)
        if not col_nascita_left:
            col_nascita_left, col_nascita_right = int(img_width * 0.60), int(img_width * 0.85)
            
        # FASE 2: Raggruppamento dei frammenti di testo per Righe Orizzontali (Y)
        righe_mappate = {}
        
        for i in range(n_elementi):
            testo_parola = str(dati_ocr['text'][i]).strip()
            confidenza = int(dati_ocr['conf'][i])
            
            if confidenza < 40 or len(testo_parola) < 2:
                continue
                
            x_pos = dati_ocr['left'][i]
            y_pos = dati_ocr['top'][i]
            
            # Troviamo o creiamo una riga orizzontale con tolleranza di 12 pixel per le oscillazioni della penna
            riga_y = None
            for y_chiave in righe_mappate.keys():
                if abs(y_chiave - y_pos) <= 12:
                    riga_y = y_chiave
                    break
            
            if riga_y is None:
                riga_y = y_pos
                righe_mappate[riga_y] = {"nomi": [], "nascita": []}
                
            # Distribuiamo la parola nella colonna corretta in base alla coordinata X
            if col_nomi_left <= x_pos <= col_nomi_right:
                if not any(x in testo_parola.upper() for x in ["COGNOME", "NOME", "ALLENATORE", "ALL"]):
                    righe_mappate[riga_y]["nomi"].append(testo_parola)
            elif col_nascita_left <= x_pos <= col_nascita_right:
                if not any(x in testo_parola.upper() for x in ["NASCITA", "DATA", "ANNO"]):
                    righe_mappate[riga_y]["nascita"].append(testo_parola)
                    
            # Rilevamento isolato dell'allenatore
            if "ALLENATORE" in testo_parola.upper() or "ALL." in testo_parola.upper():
                all_nome = "RILEVATO" # Segnaposto da sovrascrivere con i dati successivi sulla stessa Y
        
        # FASE 3: Ricostruzione e Formattazione Finale
        for y in sorted(righe_mappate.keys()):
            blocco_nomi = " ".join(righe_mappate[y]["nomi"]).strip()
            blocco_nascita = "".join(righe_mappate[y]["nascita"]).strip()
            
            if not blocco_nomi:
                continue
                
            # Estrazione pulita dell'anno di nascita (2 o 4 cifre finali della data)
            match_anno = re.search(r'\b(\d{2,4})\b', blocco_nascita)
            anno_formattato = f"'{match_anno.group(1)[-2:]}" if match_anno else ""
            
            # Formattazione estetica Nome e Cognome
            parole_anagrafica = blocco_nomi.split()
            if len(parole_anagrafica) >= 2:
                cognome = parole_anagrafica[0].upper()
                nome = " ".join(parole_anagrafica[1:]).title()
                giocatore_completo = f"{cognome} {nome}"
                if anno_formattato:
                    giocatore_completo += f" ({anno_formattato})"
                
                giocatori_estratti.append(giocatore_completo)
                
    except Exception as e:
        st.error(f"Errore durante l'estrazione geometrica: {str(e)}")
        
    # Rimozione duplicati strutturali e normalizzazione a 20 righe per Streamlit
    giocatori_estratti = [g for g in giocatori_estratti if g.strip()]
    while len(giocatori_estratti) < 20:
        giocatori_estratti.append("")
        
    return giocatori_estratti[:20], all_nome, squadra_nome


if foto_casa and foto_ospite:
    if st.button("🔍 1. ESTRAI E RIVEDERE I DATI DALLE FOTO", use_container_width=True):
        with st.spinner("Il motore semantico sta analizzando la struttura anagrafica delle foto..."):
            g_casa, a_casa, name_casa = esegui_ocr_foto_reale(foto_casa)
            g_ospite, a_ospite, name_ospite = esegui_ocr_foto_reale(foto_ospite)
            
            st.session_state.casa_giocatori_input = g_casa
            st.session_state.casa_all_input = a_casa
            st.session_state.squadra_casa_nome = name_casa
            st.session_state.ospite_giocatori_input = g_ospite
            st.session_state.ospite_all_input = a_ospite
            st.session_state.squadra_ospite_nome = name_ospite
            st.session_state.dati_pronti = True


if st.session_state.dati_pronti:
    st.markdown("---")
    
    if st.button("🔄 INVERTI SQUADRA CASA / OSPITE", use_container_width=True):
        st.session_state.squadra_casa_nome, st.session_state.squadra_ospite_nome = st.session_state.squadra_ospite_nome, st.session_state.squadra_casa_nome
        st.session_state.casa_all_input, st.session_state.ospite_all_input = st.session_state.ospite_all_input, st.session_state.casa_all_input
        st.session_state.casa_giocatori_input, st.session_state.ospite_giocatori_input = st.session_state.ospite_giocatori_input, st.session_state.casa_giocatori_input
        st.rerun()

    st.warning("📝 **Pannello di Controllo Segreteria:** Dati estratti automaticamente dalle foto. Verifica le caselle e correggi eventuali piccoli refusi prima di stampare.")
    
    edit_col1, edit_col2 = st.columns(2)
    lista_casa_corretta = []
    lista_ospite_corretta = []
    
    with edit_col1:
        st.subheader("Modifica SQUADRA CASA")
        nome_squadra_casa = st.text_input("Nome Società Ospitante (CASA)", st.session_state.squadra_casa_nome)
        c_all_edit = st.text_input("Allenatore Casa", st.session_state.casa_all_input)
        st.markdown("**Giocatori (Progressione automatica):**")
        for idx, player in enumerate(st.session_state.casa_giocatori_input):
            p_val = st.text_input(f"Casa - N. {idx+1}", value=player, key=f"c_p_{idx}")
            lista_casa_corretta.append(p_val)
            
    with edit_col2:
        st.subheader("Modifica SQUADRA OSPITE")
        nome_squadra_ospite = st.text_input("Nome Società Ospite (OSPITE)", st.session_state.squadra_ospite_nome)
        o_all_edit = st.text_input("Allenatore Ospite", st.session_state.ospite_all_input)
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
            
        corpo_tabella.append([
            Paragraph(f"<b>ALL:</b> {c_all_edit}", td_style),
            Paragraph(f"<b>ALL:</b> {o_all_edit}", td_style)
        ])
        
        t_giocatori = Table(corpo_tabella, colWidths=[267, 268])
        t_giocatori.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#1A365D')),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor('#C53030')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F7FAFC')])
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
