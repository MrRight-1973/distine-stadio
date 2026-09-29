import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from utils import pulisci_testo

def genera_pdf(casa, ospite, info_gara, qr_code_bytes=None):
    """Genera il file PDF A4 con colonne affiancate e stile personalizzato Azzurra Due Carrare"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    # --- CONFIGURAZIONE COLORI SOCIETÀ AZZURRA DUE CARRARE ---
    AZZURRO_MAIN = colors.HexColor("#0096FF")     # Azzurro brillante ufficiale per titoli principali e bordi
    AZZURRO_LIGHT = colors.HexColor("#E6F2FF")    # Sfondo soft per testate tabelle e celle numeriche
    TESTO_SCURO = colors.HexColor("#1A202C")      # Grigio antracite molto scuro per massima leggibilità
    GRIGIO_BORDI = colors.HexColor("#CBD5E0")     # Grigio chiaro pulito per le griglie interne
    
    # --- CONFIGURAZIONE STILI DI TESTO ---
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, leading=17, textColor=AZZURRO_MAIN, spaceAfter=2)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=TESTO_SCURO)
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=10, leading=12, textColor=AZZURRO_MAIN, spaceBefore=4, spaceAfter=2)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8, leading=9.5, textColor=TESTO_SCURO)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8, leading=9.5, fontName="Helvetica-Bold", textColor=TESTO_SCURO)
    qr_text_style = ParagraphStyle('QrText', parent=styles['Normal'], fontSize=6.5, leading=8, textColor=TESTO_SCURO, fontName="Helvetica-Bold", alignment=1)
    
    elementi_sinistra = [
        Paragraph("<b>DISTINTA DI GARA UFFICIALE LND</b>", title_style),
        Spacer(1, 4)
    ]
    
    tabella_info_dati = [
        [Paragraph(f"<b>CAMPIONATO:</b> {pulisci_testo(info_gara['campionato'])}", info_style), Paragraph(f"<b>DATA GARA:</b> {pulisci_testo(info_gara['data'])}", info_style)],
        [Paragraph(f"<b>ARBITRO:</b> {pulisci_testo(info_gara['arbitro'])}", info_style), Paragraph(f"<b>ASSISTENTE 1:</b> {pulisci_testo(info_gara['assistente1'])}", info_style)],
        [Paragraph("", info_style), Paragraph(f"<b>ASSISTENTE 2:</b> {pulisci_testo(info_gara['assistente2'])}", info_style)]
    ]
    t_info = Table(tabella_info_dati, colWidths=[225, 225])
    t_info.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
    ]))
    elementi_sinistra.append(t_info)
    
    if qr_code_bytes:
        buf_qr = io.BytesIO(qr_code_bytes)
        img_qr_pdf = RLImage(buf_qr, width=50, height=50)
        blocco_qr_dati = [
            [img_qr_pdf],
            [Paragraph("INQUADRA DA SMARTPHONE", qr_text_style)]
        ]
        t_blocco_qr = Table(blocco_qr_dati, colWidths=[100])
        t_blocco_qr.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))
        tabella_header_dati = [[elementi_sinistra, t_blocco_qr]]
        t_header = Table(tabella_header_dati, colWidths=[450, 100])
    else:
        tabella_header_dati = [[elementi_sinistra, ""]]
        t_header = Table(tabella_header_dati, colWidths=[450, 100])
        
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, AZZURRO_MAIN), # Linea di divisione azzurra spessa sotto l'intestazione
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 4))
    
    def genera_tabella_squadra(dati, etichetta):
        elementi_squadra = []
        elementi_squadra.append(Paragraph(f"<b>{etichetta}</b>", team_title_style))
        elementi_squadra.append(Paragraph(f"<b>{pulisci_testo(dati.get('squadra', 'N.D.'))}</b>", team_title_style))
        elementi_squadra.append(Paragraph(f"<b>ALLENATORE:</b> {pulisci_testo(dati.get('allenatore', 'NON INDICATO'))}", normal_style))
        elementi_squadra.append(Spacer(1, 3))
        
        tabella_dati = [[Paragraph("<b>N°</b>", bold_style), Paragraph("<b>GIOCATORE</b>", bold_style), Paragraph("<b>ANNO</b>", bold_style)]]
        stili_celle = [
            ('BACKGROUND', (0,0), (-1,0), AZZURRO_LIGHT), # Sfondo azzurro chiaro per la testata dei giocatori
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
            ('TOPPADDING', (0,0), (-1,-1), 1.8),
            ('GRID', (0,0), (-1,-1), 0.5, GRIGIO_BORDI),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]
        
        for index, g in enumerate(dati.get('giocatori', [])):
            testo_num = Paragraph(str(g.get('N°', index + 1)), bold_style) # Numero in grassetto
            testo_nome = Paragraph(pulisci_testo(g.get('GIOCATORE', '')), normal_style)
            testo_anno = Paragraph(str(g.get('ANNO', '')), normal_style)
            tabella_dati.append([testo_num, testo_nome, testo_anno])
            
        t = Table(tabella_dati, colWidths=[25, 190, 45])
        t.setStyle(TableStyle(stili_celle))
        elementi_squadra.append(t)
        return elementi_squadra

    colonna_casa = genera_tabella_squadra(casa, "SQUADRA OSPITANTE (CASA)")
    colonna_ospite = genera_tabella_squadra(ospite, "SQUADRA OSPITE")
    
    macro_tabella_dati = [[colonna_casa, Paragraph("", normal_style), colonna_ospite]]
    macro_tabella = Table(macro_tabella_dati, colWidths=[260, 35, 260])
    macro_tabella.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(macro_tabella)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
