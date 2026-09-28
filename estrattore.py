import base64
import json
import io
import re
from PIL import Image
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def pulisci_testo(testo):
    """Rimuove i caratteri speciali come _ e converte tutto in MAIUSCOLO"""
    if not testo or str(testo).strip() == "":
        return ""
    testo_pulito = str(testo).replace("_", " ")
    testo_pulito = re.sub(r'\s+', ' ', testo_pulito)
    return testo_pulito.strip().upper()

def encode_image(uploaded_file):
    """Apre l'immagine, la ridimensiona se troppo grande e la converte in stringa Base64"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1600, 1600))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=85)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI ed estrae i dati in formato JSON garantendo 20 righe strutturate"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        "Sei un assistente esperto di calcio LND. Il tuo compito è scansionare la griglia dei calciatori. "
        "Rispondi ESCLUSIVAMENTE con un blocco json avente questa esatta struttura:\n"
        "{\n"
        "  \"squadra\": \"Nome Squadra\",\n"
        "  \"allenatore\": \"Cognome Nome\",\n"
        "  \"data\": \"DD/MM/YYYY\",\n"
        "  \"campionato\": \"Nome Campionato\",\n"
        "  \"giocatori\": [\n"
        "    {\"numero\": 1, \"cognome_nome\": \"ROSSI ANDREA\", \"anno_nascita\": \"2005\"}\n"
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
                    {"type": "text", "text": f"Estrai l'elenco dei giocatori per la squadra {ruolo_squadra} in formato json."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices.message.content.strip()
    if risultato_grezzo.startswith("```"):
        risultato_grezzo = re.sub(r'^```(?:json)?\n', '', risultato_grezzo)
        risultato_grezzo = re.sub(r'\n```$', '', risultato_grezzo).strip()
        
    dati = json.loads(risultato_grezzo)
    
    dati["squadra"] = pulisci_testo(dati.get("squadra", "N.D."))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", "NON INDICATO"))
    dati["campionato"] = pulisci_testo(dati.get("campionato", "NON INDICATO"))
    dati["data"] = pulisci_testo(dati.get("data", "NON INDICATO"))
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                giocatori_estratti[num] = {
                    "cognome_nome": pulisci_testo(g.get("cognome_nome", "")),
                    "anno_nascita": str(g.get("anno_nascita", ""))
                }
        except:
            continue
            
    lista_20_giocatori = []
    for i in range(1, 21):
        if i in giocatori_estratti:
            lista_20_giocatori.append({
                "N°": i,
                "GIOCATORE": giocatori_estratti[i]["cognome_nome"],
                "ANNO": giocatori_estratti[i]["anno_nascita"]
            })
        else:
            lista_20_giocatori.append({"N°": i, "GIOCATORE": "", "ANNO": ""})
            
    dati["giocatori"] = lista_20_giocatori
    return dati

def genera_pdf(casa, ospite, info_gara, qr_code_bytes=None):
    """Genera il file PDF A4 con colonne affiancate e QR code integrato"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=15, leading=17, textColor=colors.HexColor("#1A365D"), spaceAfter=2)
    info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor("#2D3748"))
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=10, leading=12, textColor=colors.HexColor("#2B6CB0"), spaceBefore=4, spaceAfter=2)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=8, leading=9.5)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=8, leading=9.5, fontName="Helvetica-Bold")
    qr_text_style = ParagraphStyle('QrText', parent=styles['Normal'], fontSize=6.5, leading=8, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold", alignment=1)
    
    elementi_sinistra = [
        Paragraph("<b>DISTINTA DI GARA UFFICIALE LND</b>", title_style),
        Spacer(1, 4)
    ]
    
    tabella_info_dati = [
        [Paragraph(f"<b>CAMPIONATO:</b> {pulisci_testo(info_gara['campionato'])}", info_style), Paragraph(f"<b>DATA GARA:</b> {pulisci_testo(info_gara['data'])}", info_style)],
        [Paragraph(f"<b>ARBITRO:</b> {pulisci_testo(info_gara['arbitro'])}", info_style), Paragraph(f"<b>ASSISTENTE 1:</b> {pulisci_testo(info_gara['assistente1'])}", info_style)],
        [Paragraph("", info_style), Paragraph(f"<b>ASSISTENTE 2:</b> {pulisci_testo(info_gara['assistente2'])}", info_style)]
    ]
    t_info = Table(tabella_info_dati, colWidths=[240, 240])
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
        t_blocco_qr = Table(blocco_qr_dati, colWidths=[70])
        t_blocco_qr.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))
        tabella_header_dati = [[elementi_sinistra, t_blocco_qr]]
        t_header = Table(tabella_header_dati, colWidths=[480, 70])
    else:
        tabella_header_dati = [[elementi_sinistra, ""]]
        t_header = Table(tabella_header_dati, colWidths=[550, 0])
        
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
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
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
            ('TOPPADDING', (0,0), (-1,-1), 1.8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]
        
        for index, g in enumerate(dati.get('giocatori', [])):
            testo_num = Paragraph(str(g.get('N°', index + 1)), normal_style)
            testo_nome = Paragraph(pulisci_testo(g.get('GIOCATORE', '')), normal_style)
            testo_anno = Paragraph(str(g.get('ANNO', '')), normal_style)
            tabella_dati.append([testo_num, testo_nome, testo_anno])
            
        t = Table(tabella_dati, colWidths=[25, 195, 45])
        t.setStyle(TableStyle(stili_celle))
        elementi_squadra.append(t)
        return elementi_squadra

    colonna_casa = genera_tabella_squadra(casa, "SQUADRA OSPITANTE (CASA)")
    colonna_ospite = genera_tabella_squadra(ospite, "SQUADRA OSPITE")
    
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
