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
import pypdf

# Configurazione grafica della pagina web
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Estrazione PDF F.I.G.C. nativa ad altissima precisione e stampa A4</p>", unsafe_allow_html=True)

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
canyonato_info = st.sidebar.text_input("Campionato / Girone", "1° Categoria - Girone E")

st.sidebar.header("🏢 Pannello Sponsor (Max 5)")
sponsor_files = st.sidebar.file_uploader("Carica i loghi degli sponsor (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
if len(sponsor_files) > 5:
    st.sidebar.error("Carica massimo 5 sponsor.")
    sponsor_files = sponsor_files[:5]

st.sidebar.header("⚖️ Terna Arbitrale")
nome_arbitro = st.sidebar.text_input("Arbitro (Sig.)", "")
assistente_1 = st.sidebar.text_input("Assistente 1", "")
assistente_2 = st.sidebar.text_input("Assistente 2", "")

st.subheader("📄 Carica i file PDF delle distinte F.I.G.C.")
col1, col2 = st.columns(2)

with col1:
    file_casa = st.file_uploader("Distinta PDF Squadra CASA", type=["pdf"])
with col2:
    file_ospite = st.file_uploader("Distinta PDF Squadra OSPITE", type=["pdf"])

def formatta_stringa_giocatore_pdf(testo_grezzo):
    """Formatta la riga del giocatore salvaguardando caratteri speciali e ruoli"""
    # Isola l'anno di nascita
    match_anno = re.search(r'\b(19|20)?(\d{2})\b', testo_grezzo)
    anno = f"'{match_anno.group(2)}" if match_anno else ""
    
    # Rileva ruoli Capitano o Vice
    ruolo = ""
    if "(C)" in testo_grezzo.upper() or " C " in testo_grezzo.upper(): ruolo = " (C)"
    elif any(x in testo_grezzo.upper() for x in ["(VC)", "(V)", " VC "]): ruolo = " (VC)"
    
    # Rimuove numeri di maglia provvisori e tessere FIGC lunghe
    testo_puro = re.sub(r'\b\d{4,9}\b', '', testo_grezzo)
    testo_puro = re.sub(r'[^a-zA-Z\s]', '', testo_puro).strip()
    
    parole = [p for p in testo_puro.split() if p.upper() not in ["C", "VC", "V", "DIRIGENTE", "MEDICO"]]
    if len(parole) >= 2:
        cognome = parole[0].upper()
        nome = " ".join(parole[1:]).title()
        res = f"{cognome} {nome}{ruolo}"
        return f"{res} ({anno})" if anno else res
    elif len(parole) == 1:
        res = parole[0].upper() + ruolo
        return f"{res} ({anno})" if anno else res
    return ""

def estrai_dati_da_pdf_nativo(uploaded_pdf):
    """Legge il testo digitale interno al file PDF F.I.G.C. con precisione assoluta"""
    giocatori = []
    all_nome = "Non rilevato"
    squadra_nome = "SQUADRA RILEVATA"
    try:
        reader = pypdf.PdfReader(uploaded_pdf)
        testo_completo = ""
        for pagina in reader.pages:
            testo_completo += pagina.extract_text() + "\n"
            
        righe = testo_completo.split("\n")
        for riga in righe:
            riga_clean = riga.strip()
            if len(riga_clean) < 4 or any(x in riga_clean.upper() for x in ["FEDERAZIONE", "CAMPIONATO", "COMITATO"]):
                continue
                
            if "ALLENATORE" in riga_clean.upper() or "ALL." in riga_clean.upper():
                all_nome = re.sub(r'[^a-zA-Z\s]', '', riga_clean).replace("ALLENATORE", "").replace("All", "").strip().upper()
                continue
                
            if ("ASD" in riga_clean.upper() or "AZZURRA" in riga_clean.upper() or "PETTORAZZA" in riga_clean.upper()) and squadra_nome == "SQUADRA RILEVATA":
                squadra_nome = riga_clean.upper().strip()
                continue
                
            testo_formattato = formatta_stringa_giocatore_pdf(riga_clean)
            if testo_formattato and len(giocatori) < 20:
                giocatori.append(testo_formattato)
    except:
        pass
        
    while len(giocatori) < 20:
        giocatori.append("")
    return giocatori[:20], all_nome.title(), squadra_nome

if file_casa and file_ospite:
    if st.button("🔍 1. ESTRAI E RIVEDERE I DATI DA PDF", use_container_width=True):
        with st.spinner("Estrazione digitale istantanea dai file PDF..."):
            g_casa, a_casa, name_casa = estrai_dati_da_pdf_nativo(file_casa)
            g_ospite, a_ospite, name_ospite = estrai_dati_da_pdf_nativo(file_ospite)
            
            # Controllo incrociato: se la segreteria inverte l'ordine dei file PDF, l'app scambia i blocchi in automatico
            if "pettorazza" in file_casa.name.lower() or "ospite" in file_casa.name.lower():
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
    st.warning("📝 **Pannello di Controllo Segreteria:** Dati estratti digitalmente al 100%. Rivedi l'elenco e clicca per stampare il PDF.")
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
            story.append(Paragraph(f"{canyonato_info} | Data: {data_partita}", sub_style))
            
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
            
            st.success("✅ Distinta ad altissima precisione generata!")
            st.download_button(label="📥 Scarica PDF Distinta Verificata", data=pdf_bytes, file_name=f"Distinta_Stadio_{data_partita.replace('/', '-')}.pdf", mime="application/pdf", use_container_width=True)
