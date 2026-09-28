import streamlit as st
import base64
import json
import io
import qrcode
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara")
st.write("Carica le distinte di entrambe le squadre per generare il PDF unico con QR Code.")

client = OpenAI()

def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra):
    base64_image = encode_image(uploaded_file)
    prompt_sistema = (
        "Sei un assistente esperto di calcio LND. Analizza la distinta gara e restituisci un oggetto JSON. "
        "Devi estrarre:\n"
        "1. Il NOME DELLA SQUADRA.\n"
        "2. Il NOME E COGNOME DELL'ALLENATORE (cerca la riga Allenatore/Coach).\n"
        "3. La lista di tutti i GIOCATORI con 'cognome_nome' e 'anno_nascita' (ignora altri dirigenti).\n\n"
        "Rispondi ESCLUSIVAMENTE con questo formato JSON:\n"
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
                    {"type": "text", "text": f"Estrai i dati della squadra {ruolo_squadra} da questa distinta."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    return json.loads(response.choices[0].message.content)

def genera_pdf(casa, ospite):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    # Stili personalizzati
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor("#1A365D"), alignment=1, spaceAfter=20)
    team_title_style = ParagraphStyle('TeamTitle', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor("#2B6CB0"), spaceBefore=10, spaceAfter=5)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=12)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=10, leading=12, fontName="Helvetica-Bold")
    
    story.append(Paragraph("<b>DISTINTA DI GARA UFFICIALE</b>", title_style))
    story.append(Spacer(1, 15))
    
    def componi_sezione_squadra(dati, etichetta):
        story.append(Paragraph(f"<b>{etichetta}: {dati.get('squadra', 'N.D.').upper()}</b>", team_title_style))
        story.append(Paragraph(f"<b>Allenatore:</b> {dati.get('allenatore', 'Non indicato')}", normal_style))
        story.append(Spacer(1, 8))
        
        tabella_dati = [[Paragraph("<b>Giocatore</b>", bold_style), Paragraph("<b>Anno</b>", bold_style)]]
        for g in dati.get('giocatori', []):
            tabella_dati.append([Paragraph(g['cognome_nome'], normal_style), Paragraph(str(g['anno_nascita']), normal_style)])
            
        t = Table(tabella_dati, colWidths=[350, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

    componi_sezione_squadra(casa, "SQUADRA OSPITANTE (CASA)")
    componi_sezione_squadra(ospite, "SQUADRA OSPITE")
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- INTERFACCIA WEB ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏠 Squadra in Casa")
    file_casa = st.file_uploader("Carica distinta LOCALE", type=["png", "jpg", "jpeg"], key="casa")
    if file_casa:
        st.image(file_casa, use_container_width=True)

with col2:
    st.subheader("🚀 Squadra Ospite")
    file_ospite = st.file_uploader("Carica distinta OSPITE", type=["png", "jpg", "jpeg"], key="ospite")
    if file_ospite:
        st.image(file_ospite, use_container_width=True)

if file_casa and file_ospite:
    if st.button("⚡ Elabora e Genera PDF con QR Code", type="primary"):
        with st.spinner("Estrazione dati e creazione PDF in corso..."):
            try:
                dati_casa = analizza_distinta(file_casa, "CASA")
                dati_ospite = analizza_distinta(file_ospite, "OSPITE")
                
                # Genera il file PDF in memoria
                pdf_data = genera_pdf(dati_casa, dati_ospite)
                
                # Per rendere il file scaricabile al volo, creiamo un URL fittizio basato sui dati del file (Data URI)
                # Questo permette lo scaricamento immediato via QR Code senza configurare database esterni!
                b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                pdf_url = f"data:application/pdf;base64,{b64_pdf}"
                
                st.success("🎉 Distinte elaborate ed unite con successo!")
                
                # Visualizzazione risultati nell'app
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**⚽ Gara:** {dati_casa['squadra']} vs {dati_ospite['squadra']}")
                    st.write(f"**📋 Allenatore Casa:** {dati_casa['allenatore']}")
                    st.write(f"**📋 Allenatore Ospite:** {dati_ospite['allenatore']}")
                    
                    st.download_button(
                        label="💾 Scarica PDF su questo PC",
                        data=pdf_data,
                        file_name="riepilogo_distinte.pdf",
                        mime="application/pdf"
                    )
                
                with c2:
                    st.markdown("### 📱 Scarica su Smartphone")
                    st.write("Inquadra questo QR Code con la fotocamera del telefono per scaricare subito il PDF:")
                    
                    # Genera l'immagine del QR Code associata al file PDF codificato
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(pdf_url)
                    qr.make(fit=True)
                    img_qr = qr.make_image(fill_color="black", back_color="white")
                    
                    # Converte il QR Code per Streamlit
                    buf_qr = io.BytesIO()
                    img_qr.save(buf_qr, format="PNG")
                    st.image(buf_qr.getvalue(), width=220)
                    
            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")
