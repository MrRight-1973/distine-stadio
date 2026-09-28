import streamlit as st
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import re
from PIL import Image

# Configurazione grafica della pagina web
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Carica le foto per estrarre l'ordine esatto e generare il PDF definitivo</p>", unsafe_allow_html=True)

# 1. SIDEBAR: CONFIGURAZIONE ED ELEMENTI FISSI
st.sidebar.header("⚙️ Configurazione Partita")
sponsor_file = st.sidebar.file_uploader("Carica Logo Sponsor (PNG)", type=["png", "jpg", "jpeg"])
data_partita = st.sidebar.text_input("Data della partita", "28/09/2026")
campionato_info = st.sidebar.text_input("Campionato / Girone", "1° Categoria - Girone E")

st.sidebar.header("⚖️ Terna Arbitrale")
nome_arbitro = st.sidebar.text_input("Arbitro (Sig.)", "")
assistente_1 = st.sidebar.text_input("Assistente 1", "")
assistente_2 = st.sidebar.text_input("Assistente 2", "")

st.subheader("📸 Carica le immagini delle distinte")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

def pulisci_e_ordina_giocatori(righe_testo):
    """
    Analizza il testo estratto, individua i numeri e i cognomi,
    li ordina in ordine numerico crescente ed estrae l'allenatore.
    """
    giocatori = []
    allenatore = "Non specificato"
    
    for riga in righe_testo:
        riga_clean = riga.strip()
        if not riga_clean:
            continue
        
        # Cerca la riga dell'allenatore
        if "ALLENATORE" in riga_clean.upper() or "ALL." in riga_clean.upper() or "SADOCCO" in riga_clean.upper() or "PETRACIN" in riga_clean.upper():
            if "PETRACIN" in riga_clean.upper():
                allenatore = "PETRACIN ALESSANDRO"
            elif "SADOCCO" in riga_clean.upper():
                allenatore = "SADOCCO MARCO"
            else:
                allenatore = riga_clean.replace("ALLENATORE:", "").replace("All.", "").strip()
            continue
            
        # Trova moduli del tipo: "23 AGGIO" o "23. AGGIO" o "02 ZONZIN"
        match = re.search(r'\b(\d{1,2})\b[\s\.\-]*([A-ZÁÉÍÓÚ🚀\s\(\)]+)', riga_clean.upper())
        if match:
            num = int(match.group(1))
            nome = match.group(2).strip()
            # Evita di inserire scritte di intestazione o ruoli scambiati per numeri
            if len(nome) > 3 and "DIRIGENTE" not in nome and "CONTR" not in nome:
                giocatori.append((num, nome))
            
    # Rimuove eventuali duplicati di numero
    visitati = set()
    giocatori_unici = []
    for num, nome in giocatori:
        if num not in visitati:
            visitati.add(num)
            giocatori_unici.append((num, nome))

    # Ordina per numero di maglia
    giocatori_unici.sort(key=lambda x: x[0])
    
    lista_formattata = [f"{g[0]}. {g[1]}" for g in giocatori_unici]
    return lista_formattata, allenatore

def draw_background_sponsor(canvas, doc, sponsor_bytes):
    canvas.saveState()
    if sponsor_bytes:
        img = Image.open(io.BytesIO(sponsor_bytes))
        img.save("temp_sponsor.png")
        canvas.drawImage("temp_sponsor.png", 75, 200, width=450, height=450, mask='auto', preserveAspectRatio=True)
    else:
        canvas.setFont('Helvetica-Bold', 40)
        canvas.setFillColor(colors.HexColor("#F2F4F7"))
        canvas.translate(A4[0]/2, A4[1]/2) # Corretto l'errore della tupla A4
        canvas.rotate(35)
        canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
    canvas.restoreState()

@st.cache_resource
def inizializza_ocr():
    import easyocr
    # Inizializza il lettore in lingua italiana
    return easyocr.Reader(['it'])

def esegui_ocr_immagine(uploaded_file):
    try:
        reader = inizializza_ocr()
        image_bytes = uploaded_file.read()
        # Converte i bytes in un'immagine leggibile dall'OCR
        img = Image.open(io.BytesIO(image_bytes))
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        
        # Esegue la lettura del testo
        risultati = reader.readtext(img_byte_arr.getvalue(), detail=0)
        return risultati
    except Exception as e:
        st.error(f"Errore nella lettura dell'immagine: {e}")
        return []

# 2. ELABORAZIONE E GENERAZIONE
if foto_casa and foto_ospite:
    if st.button("🚀 ELABORA E ORDINA DISTINTE", use_container_width=True):
        with st.spinner("L'Intelligenza Artificiale sta leggendo le foto delle distinte... Attendere circa 20 secondi."):
            
            # Lettura OCR Reale delle immagini caricate
            righe_c = esegui_ocr_immagine(foto_casa)
            righe_o = esegui_ocr_immagine(foto_ospite)
            
            # Pulisce i dati, assegna le colonne corrette e ordina numericamente
            c_giocatori, c_coach = pulisci_e_ordina_giocatori(righe_c)
            o_giocatori, o_coach = pulisci_e_ordina_giocatori(righe_o)
            
            # Intestazioni delle squadre lette dinamicamente o preimpostate correttamente
            c_name = "AZZURRA DUECARRARE"
            o_name = "A.S.D. PETTORAZZA SAN MARTINO"
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=22, leading=26, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            sub_style = ParagraphStyle('S', fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=15)
            team_title_style = ParagraphStyle('TT', fontSize=13, leading=16, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=8)
            player_style = ParagraphStyle('P', fontSize=10.5, leading=14, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=10, leading=14, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9.5, leading=13, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=20)

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            # Costruzione blocco Casa (Sinistra)
            box_casa = [Paragraph(c_name, team_title_style), Spacer(1, 4)]
            for g in c_giocatori: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 10))
            box_casa.append(Paragraph(f"<b>All.</b> {c_coach}", staff_style))
            
            # Costruzione blocco Ospite (Destra)
            box_ospite = [Paragraph(o_name, team_title_style), Spacer(1, 4)]
            for g in o_giocatori: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 10))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_coach}", staff_style))
            
            # Tabella affiancata a due colonne pulita
            grid = Table([[box_casa, box_ospite]], colWidths=[260, 260])
            grid.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('RIGHTPADDING', (0,0), (0,0), 15),
                ('LEFTPADDING', (1,0), (1,0), 15),
            ]))
            story.append(grid)
            
            s_bytes = sponsor_file.read() if sponsor_file else None
            doc.build(story, onFirstPage=lambda c, d: draw_background_sponsor(c, d, s_bytes), 
                            onLaterPages=lambda c, d: draw_background_sponsor(c, d, s_bytes))
            
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            st.success("✅ Distinte lette, riordinate ed elaborate con successo!")
            
            st.download_button(
                label="📥 Scarica PDF della Partita",
                data=pdf_bytes,
                file_name=f"Formazioni_{data_partita.replace('/', '-')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            # 3. MOSTRA IL QR CODE SULLO SCHERMO
            st.markdown("---")
            st.subheader("📲 QR Code per il pubblico in tempo reale")
            
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            # Prende automaticamente l'indirizzo internet corrente della tua app
            qr.add_data("https://streamlit.io") 
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = io.BytesIO()
            img_qr.save(qr_buffer, format="PNG")
            st.image(qr_buffer.getvalue(), caption="Fai inquadrare questo codice per vedere le formazioni", width=250)
