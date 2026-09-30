import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from utils import pulisci_testo

def genera_pdf(casa, ospite, info_gara, qr_code_bytes=None):
    """Genera il file PDF A4 strutturato con tabelle affiancate e QR code."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    # Definizione Stili grafici
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, leading=17, textColor=colors.HexColor("#1A365D"), spaceAfter=2)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor("#2D3748"))
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=10, leading=12, textColor=colors.HexColor("#2B6CB0"), spaceBefore=4, spaceAfter=2)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8, leading=9.5)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8, leading=9.5, fontName="Helvetica-Bold")
    qr_text_style = ParagraphStyle('QrText', parent=styles['Normal'], fontSize=6.5, leading=8, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold", alignment=1)
    
    # Costruzione Blocco Intestazione (Sinistra)
    elementi_sinistra = [
        Paragraph("<b>DISTINTA DI GARA UFFICIALE LND</b>", title_style),
        Spacer(1, 4)
    ]
    
    tabella_info_dati = [
        [Paragraph(f"<b>CAMPIONATO:</b> {pulisci_testo(info_gara['campionato'])}", info_style), Paragraph(f"<b>DATA GARA:</b> {pulisci_testo(info_gara['data'])}", info_style)],
        [Paragraph(f"<b>ARBITRO:</b> {pulisci_testo(info_gara['arbitro'])}", info_style), Paragraph(f"<b>ASSISTENTE 1:</b> {pulisci_testo(info_gara['assistente1'])}", info_style)],
        [Paragraph("", info_style), Paragraph(f"<b>ASSISTENTE 2:</b> {pulisci_testo(info_gara['assistente2'])}", info_style)]
    ]
    t_info = Table(tabella_info_dati, colWidths=[180, 180])
    t_info.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
    ]))
    elementi_sinistra.append(t_info)
    
    # Integrazione QR Code (Destra)
    if qr_code_bytes:
        buf_qr = io.BytesIO(qr_code_bytes)
        img_qr_pdf = RLImage(buf_qr, width=50, height=50)
        blocco_qr_dati = [[img_qr_pdf], [Paragraph("INQUADRA DA SMARTPHONE", qr_text_style)]]
        t_blocco_qr = Table(blocco_qr_dati, colWidths=[100])
        t_blocco_qr.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))
        t_header = Table([[elementi_sinistra, t_blocco_qr]], colWidths=[450, 100])
    else:
        t_header = Table([[elementi_sinistra, ""]], colWidths=[450, 100])
        
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 4))
    
    # Funzione interna per generare la griglia dei 20 giocatori
    def genera_tabella_squadra(dati, etichetta):
        elementi_squadra = [
            Paragraph(f"<b>{etichetta}</b>", team_title_style),
            Paragraph(f"<b>{pulisci_testo(dati.get('squadra', 'N.D.'))}</b>", team_title_style),
            Paragraph(f"<b>ALLENATORE:</b> {pulisci_testo(dati.get('allenatore', 'NON INDICATO'))}", normal_style),
            Spacer(1, 3)
        ]
        
        tabella_dati = [[Paragraph("<b>N°</b>", bold_style), Paragraph("<b>GIOCATORE</b>", bold_style), Paragraph("<b>ANNO</b>", bold_style)]]
        for index, g in enumerate(dati.get('giocatori', [])):
            tabella_dati.append([
                Paragraph(str(g.get('N°', index + 1)), normal_style),
                Paragraph(pulisci_testo(g.get('GIOCATORE', '')), normal_style),
                Paragraph(str(g.get('ANNO', '')), normal_style)
            ])
            
        t = Table(tabella_dati, colWidths=[30, 185, 45])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
            ('TOPPADDING', (0,0), (-1,-1), 1.8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elementi_squadra.append(t)
        return elementi_squadra

    # Affiancamento delle due colonne
    colonna_casa = genera_tabella_squadra(casa, "SQUADRA OSPITANTE (CASA)")
    colonna_ospite = genera_tabella_squadra(ospite, "SQUADRA OSPITE")
    
    macro_tabella = Table([[colonna_casa, Paragraph("", normal_style), colonna_ospite]], colWidths=[260, 30, 260])
    macro_tabella.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(macro_tabella)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
