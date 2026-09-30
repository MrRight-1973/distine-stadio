import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def genera_pdf(casa, ospite, info_gara, qr_code_bytes=None):
    buffer = io.BytesIO()
    # Margini ottimizzati a 20 punti per massimizzare lo spazio verticale su un'unica pagina A4
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    # Stili tipografici per l'intestazione e le tabelle
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, leading=16, textColor=colors.HexColor("#1A365D"), spaceAfter=2)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor("#2D3748"))
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=11, leading=13, textColor=colors.HexColor("#2B6CB0"), spaceBefore=2, spaceAfter=4)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8, leading=9.5)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8, leading=9.5, fontName="Helvetica-Bold")
    qr_text_style = ParagraphStyle('QrText', parent=styles['Normal'], fontSize=6.5, leading=8, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold", alignment=1)
    
    elementi_sinistra = [
        Paragraph("<b>DISTINTA DI GARA UFFICIALE LND</b>", title_style),
        Spacer(1, 4)
    ]
    
    # Tabella informativa centrale (Campionato, Data, Arbitro e Assistenti)
    tabella_info_dati = [
        [Paragraph(f"<b>CAMPIONATO:</b> {info_gara['campionato']}", info_style), Paragraph(f"<b>DATA GARA:</b> {info_gara['data']}", info_style)],
        [Paragraph(f"<b>ARBITRO:</b> {info_gara['arbitro']}", info_style), Paragraph(f"<b>ASSISTENTE 1:</b> {info_gara['assistente1']}", info_style)],
        [Paragraph("", info_style), Paragraph(f"<b>ASSISTENTE 2:</b> {info_gara['assistente2']}", info_style)]
    ]
    t_info = Table(tabella_info_dati, colWidths=[200, 200])
    t_info.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 1.5), ('TOPPADDING', (0,0), (-1,-1), 1.5)]))
    elementi_sinistra.append(t_info)
    
    # Gestione del Logo dell'Azzurra Due Carrare nell'angolo in alto a destra
    # Nota: Utilizziamo un URL diretto dell'immagine per massima portabilità del codice su Streamlit Cloud
    url_logo = "https://githubusercontent.com" # Sostituisci questo link con l'URL effettivo del tuo logo png se necessario
    try:
        img_logo = RLImage(url_logo, width=45, height=45)
    except:
        # Se il link non dovesse essere temporaneamente raggiungibile, crea un blocco vuoto protettivo per non far crashare l'app
        img_logo = Paragraph("", normal_style)
        
    # Gestione del QR Code affiancato al logo
    if qr_code_bytes:
        buf_qr = io.BytesIO(qr_code_bytes)
        img_qr_pdf = RLImage(buf_qr, width=45, height=45)
        t_blocco_destra = Table([
            [img_logo, img_qr_pdf],
            [Paragraph("", qr_text_style), Paragraph("INQUADRA", qr_text_style)]
        ], colWidths=[55, 55])
        t_blocco_destra.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0)
        ]))
        t_header = Table([[elementi_sinistra, t_blocco_destra]], colWidths=[440, 110])
    else:
        t_header = Table([[elementi_sinistra, img_logo]], colWidths=[495, 55])
        
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_header)
    story.append(Spacer(1, 6))
    
    def genera_tabella_squadra(dati):
        # Rimossa l'etichetta fissa "SQUADRA OSPITANTE / OSPITE". Mostra direttamente il Nome Società e l'Allenatore
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
            
        t = Table(tabella_dati, colWidths=[25, 195, 40])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
            ('TOPPADDING', (0,0), (-1,-1), 2.2),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elementi_squadra.append(t)
        return elementi_squadra

    # Creazione del blocco a due colonne affiancate perfettamente bilanciate (LND Standard)
    macro_tabella = Table([[genera_tabella_squadra(casa), Paragraph("", normal_style), genera_tabella_squadra(ospite)]], colWidths=[260, 35, 260])
    macro_tabella.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0)
    ]))
    
    story.append(macro_tabella)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
