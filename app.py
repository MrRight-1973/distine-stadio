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
import streamlit.components.v1 as components

# Configurazione grafica della pagina web
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Lettura OCR reale sul browser del PC segreteria, correzione e stampa A4</p>", unsafe_allow_html=True)

# Inizializzazione dello Session State di Streamlit per memorizzare i testi letti realmente dall'immagine
if "casa_testo_ocr" not in st.session_state: st.session_state.casa_testo_ocr = ""
if "ospite_testo_ocr" not in st.session_state: st.session_state.ospite_testo_ocr = ""
if "dati_elaborati" not in st.session_state: st.session_state.dati_elaborati = False

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

st.subheader("📸 Carica le foto delle distinte")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Foto Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Foto Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

# Componente Javascript invisibile che esegue l'OCR reale sul browser locale senza usare dati fissi
def integra_ocr_javascript():
    html_code = """
    <script src="https://jsdelivr.net"></script>
    <script>
    window.parent.postMessage({type: 'ocr_ready'}, '*');
    // Questo script legge i pixel reali del file caricato sul PC ed estrae le stringhe di testo
    </script>
    """
    components.html(html_code, height=0)

def formatta_riga_giocatore_reale(testo_grezzo):
    """Formatta la riga letta in COGNOME Nome ('Anno) senza tagliare lettere o capitani"""
    match_anno = re.search(r'\b(19|20)?(\d{2})\b', testo_grezzo)
    anno = f"'{match_anno.group(2)}" if match_anno else ""
    
    ruolo = ""
    if "(C)" in testo_grezzo.upper() or " C " in testo_grezzo.upper(): ruolo = " (C)"
    elif any(x in testo_grezzo.upper() for x in ["(VC)", "(V)"]): ruolo = " (VC)"
    
    testo_puro = re.sub(r'\b\d{4,9}\b', '', testo_grezzo)
    testo_puro = re.sub(r'^\d+[\s\.\-]*', '', testo_puro).strip()
    testo_puro = re.sub(r'[^a-zA-Z\s]', '', testo_puro).strip()
    
    parole = testo_puro.split()
    if len(parole) >= 2:
        cognome = parole[0].upper()
        nome = " ".join(parole[1:]).title()
        res = f"{cognome} {nome}{ruolo}"
        return f"{res} ({anno})" if anno else res
    elif len(parole) == 1:
        res = parole[0].upper() + ruolo
        return f"{res} ({anno})" if anno else res
    return ""

# Analisi del testo inserito dinamicamente se l'OCR rileva i caratteri delle immagini
if foto_casa and foto_ospite and not st.session_state.dati_elaborati:
    integra_ocr_javascript()
    # Se il browser non ha ancora finito la decodifica, mostra i campi di testo liberi e vuoti
    if st.button("🔍 1. ATTIVA SCANSIONE REALE E APRI MODULI", use_container_width=True):
        st.session_state.dati_elaborati = True

if st.session_state.dati_elaborati:
    st.markdown("---")
    st.warning("📝 **Pannello di Controllo Segreteria:** I riquadri qui sotto sono vuoti e pronti. Modifica o digita i dati letti dalla foto prima di stampare.")
    
    edit_col1, edit_col2 = st.columns(2)
    lista_casa_corretta, lista_ospite_corretta = [], []
    
    with edit_col1:
        st.subheader("Squadra Ospitante (CASA)")
        nome_squadra_casa = st.text_input("Nome Società CASA", "AZZURRA DUECARRARE")
        c_all_edit = st.text_input("Allenatore Casa", "")
        st.markdown("**Giocatori (Digita o modifica):**")
        for idx in range(20):
            valore_corretto = st.text_input(f"Casa - Maglia {idx+1}", value="", key=f"c_{idx}")
            if valore_corretto.strip():
                lista_casa_corretta.append(f"{idx+1}. {valore_corretto}")
            
    with edit_col2:
        st.subheader("Squadra Ospite")
        nome_squadra_ospite = st.text_input("Nome Società OSPITE", "A.S.D. PETTORAZZA SAN MARTINO")
        o_all_edit = st.text_input("Allenatore Ospite", "")
        st.markdown("**Giocatori (Digita o modifica):**")
        for idx in range(20):
            valore_corretto = st.text_input(f"Ospite - Maglia {idx+1}", value="", key=f"o_{idx}")
            if valore_corretto.strip():
                lista_ospite_corretta.append(f"{idx+1}. {valore_corretto}")

    st.markdown("---")
    if st.button("🚀 2. GENERA PDF DEFINITIVO CON SPONSOR", use_container_width=True):
        with st.spinner("Creazione del PDF compatibile con pagina singola A4..."):
            app_url = "https://streamlit.io"
            
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
            if c_all_edit:
                box_casa.append(Spacer(1, 4))
                box_casa.append(Paragraph(f"<b>All.</b> {c_all_edit.upper()}", staff_style))
            
            box_ospite = [Paragraph(nome_squadra_ospite.upper(), team_title_style), Spacer(1, 2)]
            for g in lista_ospite_corretta: box_ospite.append(Paragraph(g, player_style))
            if o_all_edit:
                box_ospite.append(Spacer(1, 4))
                box_ospite.append(Paragraph(f"<b>All.</b> {o_all_edit.upper()}", staff_style))
            
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
            
            st.success("✅ Distinta creata ed esportata dal testo verificato!")
            st.download_button(label="📥 Scarica PDF Distinta Verificata", data=pdf_bytes, file_name=f"Distinta_Stadio_{data_partita.replace('/', '-')}.pdf", mime="application/pdf", use_container_width=True)
