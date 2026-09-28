import streamlit as st
import base64
import json
import io
import qrcode
import requests
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Gestione Distinte LND", page_icon="⚽", layout="wide")

st.title("⚽ Centro Gestione Distinte Gara")
st.write("Carica le distinte di entrambe le squadre per generare il PDF unico A4 con QR Code.")

# 2. Inizializzazione del client OpenAI (legge in automatico la chiave dai Secrets di Streamlit)
client = OpenAI()

def encode_image(uploaded_file):
    """Converte il file caricato dall'utente in stringa Base64 per le API"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra):
    """Invia la foto a OpenAI ed estrae i dati strutturati in JSON"""
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
    return json.loads(response.choices.message.content)

def genera_pdf(casa, ospite):
    """Genera il file PDF formattato in un unico foglio A4 con colonne affiancate"""
    buffer = io.BytesIO()
    # Configurazione della pagina su formato A4 e margini ridotti per ottimizzare lo spazio
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
    
    # Inseriamo i due blocchi dentro una macro-tabella invisibile a 2 colonne per affiancarle (A4 ha circa 550pt utili)
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

# --- INTERFACCIA WEB (LAYOUT GRAFICO) ---
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

# Gestione elaborazione al caricamento di entrambi i file
if file_casa and file_ospite:
    st.write("")
    if st.button("⚡ Elabora e Genera PDF con QR Code", type="primary"):
        with st.spinner("Estrazione dati e creazione PDF in corso..."):
            try:
                # Esegue l'analisi delle immagini tramite AI
                dati_casa = analizza_distinta(file_casa, "CASA")
                dati_ospite = analizza_distinta(file_ospite, "OSPITE")
                
                # Genera il file PDF in memoria (Formato A4 compatto)
                pdf_data = genera_pdf(dati_casa, dati_ospite)
                
                st.success("🎉 Distinte elaborate ed unite con successo!")
                
                # Carica temporaneamente il PDF su file.io per generare il link per lo smartphone (scade in 1 giorno)
                files = {'file': ('riepilogo_distinte.pdf', pdf_data, 'application/pdf')}
                response_cloud = requests.post('https://file.io', files=files)
                
                if response_cloud.status_code == 200:
                    pdf_url = response_cloud.json().get("link")
                else:
                    pdf_url = "https://file.io"
                    st.error("Errore temporaneo nel caricamento del codice online. Scarica il PDF localmente.")

                # Mostra i risultati a schermo divisi in due sezioni pulite
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### 📋 Riepilogo Squadre")
                    st.write(f"**⚽ Gara:** {dati_casa['squadra']} vs {dati_ospite['squadra']}")
                    st.write(f"**🏠 Allenatore Casa:** {dati_casa['allenatore']}")
                    st.write(f"**🚀 Allenatore Ospite:** {dati_ospite['allenatore']}")
                    st.write("")
                    
                    st.download_button(
                        label="💾 Scarica PDF su questo PC",
                        data=pdf_data,
                        file_name="riepilogo_distinte.pdf",
                        mime="application/pdf"
                    )
                
                with c2:
                    st.markdown("### 📱 Scarica su Smartphone")
                    st.write("Inquadra questo QR Code con il telefono per salvare il PDF:")
                    
                    # Genera il QR Code dinamico (leggero e facile da scansionare sul campo)
                    qr = qrcode.QRCode(
                        version=None,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4
                    )
                    qr.add_data(pdf_url)
                    qr.make(fit=True)
                    img_qr = qr.make_image(fill_color="black", back_color="white")
                    
                    # Mostra l'immagine del QR Code nell'app
                    buf_qr = io.BytesIO()
                    img_qr.save(buf_qr, format="PNG")
                    st.image(buf_qr.getvalue(), width=220)
                    st.caption(f"Link diretto: {pdf_url}")
                    
            except Exception as e:
                st.error(f"Si è verificato un errore durante l'elaborazione: {e}")
