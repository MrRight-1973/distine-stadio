import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def genera_pdf(casa, ospite, info_gara, qr_code_bytes=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, leading=16, textColor=colors.HexColor("#1A365D"), spaceAfter=2)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor("#2D3748"))
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=11, leading=13, textColor=colors.HexColor("#2B6CB0"), spaceBefore=2, spaceAfter=4)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8, leading=9.5)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8, leading=9.5, fontName="Helvetica-Bold")
    qr_text_style = ParagraphStyle('QrText', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold", alignment=1)
    
    elementi_sinistra = [
        Paragraph("<b>DISTINTA DI GARA UFFICIALE LND</b>", title_style),
        Spacer(1, 4)
    ]
    
    tabella_info_dati = [
        [Paragraph(f"<b>CAMPIONATO:</b> {info_gara['campionato']}", info_style), Paragraph(f"<b>DATA GARA:</b> {info_gara['data']}", info_style)],
        [Paragraph(f"<b>ARBITRO:</b> {info_gara['arbitro']}", info_style), Paragraph(f"<b>ASSISTENTE 1:</b> {info_gara['assistente1']}", info_style)],
        [Paragraph("", info_style), Paragraph(f"<b>ASSISTENTE 2:</b> {info_gara['assistente2']}", info_style)]
    ]
    t_info = Table(tabella_info_dati, colWidths=[180, 180])
    t_info.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 1.5), ('TOPPADDING', (0,0), (-1,-1), 1.5)]))
    elementi_sinistra.append(t_info)
    
    # Lettura locale del logo societario con calcolo automatico dell'Aspect Ratio
    img_logo = None
    nome_file_logo = "logo_azzurra.png"
    if os.path.exists(nome_file_logo):
        try:
            # Creiamo un'istanza temporanea dell'immagine per estrarne le proporzioni native
            img_temporanea = RLImage(nome_file_logo)
            w_originale = img_temporanea.drawWidth
            h_originale = img_temporanea.drawHeight
            
            # Fissiamo la larghezza desiderata nel PDF e calcoliamo l'altezza proporzionale
            larghezza_target = 50.0
            altezza_proporzionale = (h_originale / w_originale) * larghezza_target
            
            # Generiamo l'immagine finale perfettamente proporzionata
            img_logo = RLImage(nome_file_logo, width=larghezza_target, height=altezza_proporzionale)
        except Exception:
            img_logo = None

    # Composizione dell'intestazione superiore
    if img_logo:
        t_header = Table([[elementi_sinistra, img_logo]], colWidths=[450, 100])
        t_header.setStyle(TableStyle([
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('VALIGN', (1,0), (1,0), 'MIDDLE')
        ]))
    else:
        t_header = Table([[elementi_sinistra, ""]], colWidths=[450, 100])
        
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_header)
    story.append(Spacer(1, 6))
    
    def genera_tabella_squadra(dati):
        elementi_squadra = [
            Paragraph(f"<b>{dati.get('squadra', 'SQUADRA')}</b>", team_title_style),
            Paragraph(f"<b>ALLENATORE:</b> {dati.get('allenatore', '')}", normal_style),
            Spacer(1, 5)
        ]
        
        tabella_dati = [[Paragraph("<b>N°</b>", bold_style), Paragraph("<b>GIOCATORE</b>", bold_style), Paragraph("<b>ANNO</b>", bold_style)]]
        for index, g in enumerate(dati.get('giocatori', [])):
            tabella_dati.append([
                Paragraph(str(g.get('N°', index + 1)), normal_style),
                Paragraph(str(g.get('GIOCATORE', '')), normal_style),
                Paragraph(str(g.get('ANNO', '')), normal_style)
            ])
            
        t = Table(tabella_dati, colWidths=[30, 185, 45])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
            ('TOPPADDING', (0,0), (-1,-1), 2.2),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elementi_squadra.append(t)
        return elementi_squadra

    # Inserimento delle due tabelle affiancate
    macro_tabella = Table([[genera_tabella_squadra(casa), Paragraph("", normal_style), genera_tabella_squadra(ospite)]], colWidths=[260, 30, 260])
    macro_tabella.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0)
    ]))
    story.append(macro_tabella)
    
    # Blocco QR Code centrato in fondo
    if qr_code_bytes:
        story.append(Spacer(1, 15))
        buf_qr = io.BytesIO(qr_code_bytes)
        img_qr_pdf = RLImage(buf_qr, width=90, height=90)
        
        t_qr_footer = Table([
            [img_qr_pdf],
            [Spacer(1, 3)],
            [Paragraph("INQUADRA DA SMARTPHONE PER ACCEDERE AL GESTIONALE UFFICIALE", qr_text_style)]
        ], colWidths=[550])
        
        t_qr_footer.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0)
        ]))
        story.append(t_qr_footer)
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
