from reportlab.lib.pagesizes import A4  # Assicurati che A4 sia importato in cima se non lo era già

def genera_pdf(casa, ospite):
    buffer = io.BytesIO()
    # Configurazione della pagina su formato A4 e margini ridotti a 20 punti per ottimizzare lo spazio
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    # Stili super compatti per evitare il passaggio alla seconda pagina
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=18, textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=10)
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=11, leading=13, textColor=colors.HexColor("#2B6CB0"), spaceBefore=5, spaceAfter=3)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8.5, leading=10)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8.5, leading=10, fontName="Helvetica-Bold")
    
    story.append(Paragraph("<b>DISTINTA DI GARA UFFICIALE</b>", title_style))
    story.append(Spacer(1, 5))
    
    # Creiamo una struttura a due colonne reali affiancate (Casa a sinistra, Ospite a destra)
    # Questo è il modo più sicuro in assoluto per far stare tutto in un unico foglio A4!
    
    def genera_tabella_squadra(dati, etichetta):
        elementi_squadra = []
        elementi_squadra.append(Paragraph(f"<b>{etichetta}</b>", team_title_style))
        elementi_squadra.append(Paragraph(f"<b>{dati.get('squadra', 'N.D.').upper()}</b>", team_title_style))
        elementi_squadra.append(Paragraph(f"<b>All:</b> {dati.get('allenatore', 'Non indicato')}", normal_style))
        elementi_squadra.append(Spacer(1, 4))
        
        tabella_dati = [[Paragraph("<b>Giocatore</b>", bold_style), Paragraph("<b>Anno</b>", bold_style)]]
        for g in dati.get('giocatori', []):
            tabella_dati.append([Paragraph(g['cognome_nome'], normal_style), Paragraph(str(g['anno_nascita']), normal_style)])
            
        # Larghezza colonne ottimizzata per la mezza pagina (220 totali: 180 nome, 40 anno)
        t = Table(tabella_dati, colWidths=[180, 40])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),  # Padding ridottissimo per risparmiare altezza
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elementi_squadra.append(t)
        return elementi_squadra

    # Generiamo i blocchi delle due squadre
    colonna_casa = genera_tabella_squadra(casa, "SQUADRA OSPITANTE")
    colonna_ospite = genera_tabella_squadra(ospite, "SQUADRA OSPITE")
    
    # Inseriamo i due blocchi dentro una macro-tabella invisibile a 2 colonne per affiancarle
    # Larghezza totale A4 utile circa 550 punti -> 265 a colonna + 20 di spazio centrale
    macro_tabella_dati = [[colonna_casa, Paragraph("", normal_style), colonna_ospite]]
    macro_tabella = Table(macro_tabella_dati, colWidths=[265, 20, 265])
    macro_tabella.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(macro_tabella)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
