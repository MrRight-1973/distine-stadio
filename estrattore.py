import base64
import json
import io
import re
from PIL import Image
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Inizializzazione del client OpenAI
client = OpenAI()

def encode_image(uploaded_file):
    """Apre l'immagine, la ridimensiona se troppo grande e la converte in stringa Base64"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1600, 1600))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=85)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra):
    """Invia la foto ottimizzata a OpenAI ed estrae i dati strutturati garantendo il formato"""
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        "Sei un assistente esperto di calcio LND. Analizza la distinta gara e restituisci un oggetto json valido. "
        "Devi estrarre obbligatoriamente:\n"
        "1. Il NOME DELLA SQUADRA.\n"
        "2. Il NOME E COGNOME DELL'ALLENATORE.\n"
        "3. La lista di tutti i GIOCATORI con 'cognome_nome' e 'anno_nascita'.\n\n"
        "Rispondi ESCLUSIVAMENTE con un blocco json avente questa esatta struttura:\n"
        "{\n"
        "  \"squadra\": \"Nome Squadra\",\n"
        "  \"allenatore\": \"Cognome Nome\",\n"
        "  \"giocatori\": [\n"
        "    {\"cognome_nome\": \"ROSSI ANDREA\", \"anno_nascita\": 2005}\n"
        "  ]\n"
        "}"
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Estrai i dati e formattali in un dizionario json per la squadra {ruolo_squadra} da questa immagine."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices[0].message.content
    if not risultato_grezzo:
        raise ValueError("OpenAI ha risposto con un contenuto vuoto.")
        
    risultato_grezzo = risultato_grezzo.strip()
    if risultato_grezzo.startswith("```"):
        risultato_grezzo = re.sub(r'^```(?:json)?\n', '', risultato_grezzo)
        risultato_grezzo = re.sub(r'\n```$', '', risultato_grezzo).strip()
        
    return json.loads(risultato_grezzo)

def genera_pdf(casa, ospite):
    """Genera il file PDF formattato in un unico foglio A4 con colonne affiancate ed evidenziazione Under"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=18, textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=10)
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=11, leading=13, textColor=colors.HexColor("#2B6CB0"), spaceBefore=5, spaceAfter=3)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8.5, leading=10)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8.5, leading=10, fontName="Helvetica-Bold")
    under_style = ParagraphStyle('UnderStyle', parent=styles['Normal'], fontSize=8.5, leading=10, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Oblique")
    
    story.append(Paragraph("<b>DISTINTA DI GARA UFFICIALE</b>", title_style))
    story.append(Spacer(1, 5))
    
    def genera_tabella_squadra(dati, etichetta):
        elementi_squadra = []
        elementi_squadra.append(Paragraph(f"<b>{etichetta}</b>", team_title_style))
        elementi_squadra.append(Paragraph(f"<b>{dati.get('squadra', 'N.D.').upper()}</b>", team_title_style))
        elementi_squadra.append(Paragraph(f"<b>All:</b> {dati.get('allenatore', 'Non indicato')}", normal_style))
        elementi_squadra.append(Spacer(1, 4))
        
        tabella_dati = [[Paragraph("<b>Giocatore</b>", bold_style), Paragraph("<b>Anno</b>", bold_style)]]
        stili_celle = [
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]
        
        for indice, g in enumerate(dati.get('giocatori', []), start=1):
            anno = int(g['anno_nascita'])
            if anno >= 2007:
                testo_nome = Paragraph(f"{g['cognome_nome']} 🌟 (Under)", under_style)
                testo_anno = Paragraph(f"<b>{anno}</b>", under_style)
                stili_celle.append(('BACKGROUND', (0, indice), (-1, indice), colors.HexColor("#E6FFFA")))
            else:
                testo_nome = Paragraph(g['cognome_nome'], normal_style)
                testo_anno = Paragraph(str(anno), normal_style)
            tabella_dati.append([testo_nome, testo_anno])
            
        t = Table(tabella_dati, colWidths=[180, 45])
        t.setStyle(TableStyle(stili_celle))
        elementi_squadra.append(t)
        return elementi_squadra

    colonna_casa = genera_tabella_squadra(casa, "SQUADRA OSPITANTE")
    colonna_ospite = genera_tabella_squadra(ospite, "SQUADRA OSPITE")
    
    macro_tabella_dati = [[colonna_casa, Paragraph("", normal_style), colonna_ospite]]
    macro_tabella = Table(macro_tabella_dati, colWidths=[225, 20, 225])
    macro_tabella.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(macro_tabella)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
