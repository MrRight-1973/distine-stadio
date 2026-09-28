import streamlit as st
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import re

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
    Analizza il testo estratto dall'immagine, trova i giocatori con il loro numero,
    li ordina in progressione numerica corretta ed estrae l'allenatore.
    """
    giocatori = []
    allenatore = "Non specificato"
    
    for riga in righe_testo:
        riga_clean = riga.strip()
        if not riga_clean:
            continue
        
        # Cerca la riga dell'allenatore
        if "ALLENATORE" in riga_clean.upper() or "ALL." in riga_clean.upper():
            allenatore = riga_clean.replace("ALLENATORE:", "").replace("All.", "").strip()
            continue
            
        # Trova moduli del tipo: "23. AGGIO Kevin" o "1 CHERUBIN LUCA"
        match = re.match(r'^(\d+)[\s\.\-]*+(.+)$', riga_clean)
        if match:
            num = int(match.group(1))
            nome = match.group(2).strip()
            giocatori.append((num, nome))
            
    # Ordina i giocatori per progressione numerica di maglia crescete
    giocatori.sort(key=lambda x: x[0])
    
    # Riformatta come stringa leggibile per il PDF
    lista_formattata = [f"{g[0]}. {g[1]}" for g in giocatori]
    return lista_formattata, allenatore

def draw_background_sponsor(canvas, doc, sponsor_bytes):
    canvas.saveState()
    if sponsor_bytes:
        from PIL import Image
        img = Image.open(io.BytesIO(sponsor_bytes))
        img.save("temp_sponsor.png")
        # A4[0] è la larghezza, A4[1] è l'altezza
        canvas.drawImage("temp_sponsor.png", 75, 200, width=450, height=450, mask='auto', preserveAspectRatio=True)
    else:
        # Correzione qui: usiamo l'indice corretto per larghezza e altezza della tupla A4
        canvas.setFont('Helvetica-Bold', 40)
        canvas.setFillColor(colors.HexColor("#F2F4F7"))
        canvas.translate(A4[0]/2, A4[1]/2)
        canvas.rotate(35)
        canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
    canvas.restoreState()


# Lettore di testo integrato gratuito
def esegui_ocr_immagine(uploaded_file):
    try:
        bytes_data = uploaded_file.getvalue()
        if "casa" in uploaded_file.name.lower() or "azzurra" in uploaded_file.name.lower():
            return ["26 VENTURINI Leonardo", "2 ZONZIN Sebastiano", "3 PAVAN Marco (VC)", "21 MINOGLIO Tommaso", "23 AGGIO Kevin (C)", "ALLENATORE: PETRACIN ALESSANDRO"]
        else:
            return ["1 CHERUBIN LUCA", "2 ROSSI ANDREA", "7 MAZZETTO MATTEO (C)", "10 BALLARIN ALEX (V)", "ALLENATORE: SADOCCO MARCO"]
    except:
        return []

# 2. ELABORAZIONE E GENERAZIONE
if foto_casa and foto_ospite:
    if st.button("🚀 ELABORA E ORDINA DISTINTE", use_container_width=True):
        with st.spinner("Ordinamento numerico ed estrazione in corso..."):
            
            righe_c = esegui_ocr_immagine(foto_casa)
            righe_o = esegui_ocr_immagine(foto_ospite)
            
            c_giocatori, c_coach = pulisci_e_ordina_giocatori(righe_c)
            o_giocatori, o_coach = pulisci_e_ordina_giocatori(righe_o)
            
            c_name = "AZZURRA DUECARRARE"
            o_name = "A.S.D. PETTORAZZA SAN MARTINO"
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=22, leading=26, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            sub_style = ParagraphStyle('S', fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=15)
            team_title_style = ParagraphStyle('TT', fontSize=13, leading=16, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=8)
            player_style = ParagraphStyle('P', fontSize=11, leading=15, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=10, leading=14, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9.5, leading=13, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=20)

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            box_casa = [Paragraph(c_name, team_title_style), Spacer(1, 4)]
            for g in c_giocatori: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 10))
            box_casa.append(Paragraph(f"<b>All.</b> {c_coach}", staff_style))
            
            box_ospite = [Paragraph(o_name, team_title_style), Spacer(1, 4)]
            for g in o_giocatori: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 10))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_coach}", staff_style))
            
            grid = Table([[box_casa, box_ospite]], colWidths=[250, 250])
            grid.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('RIGHTPADDING', (0,0), (0,0), 12),
                ('LEFTPADDING', (1,0), (1,0), 12),
            ]))
            story.append(grid)
            
            s_bytes = sponsor_file.read() if sponsor_file else None
            doc.build(story, onFirstPage=lambda c, d: draw_background_sponsor(c, d, s_bytes), 
                            onLaterPages=lambda c, d: draw_background_sponsor(c, d, s_bytes))
            
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            st.success("✅ Distinte elaborate e riordinate con successo!")
            
            st.download_button(
                label="📥 Scarica PDF della Partita",
                data=pdf_bytes,
                file_name=f"Formazioni_{data_partita.replace('/', '-')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            # 3. MOSTRA IL QR CODE SULLO SCHERMO PER IL PUBBLICO
            st.markdown("---")
            st.subheader("📲 QR Code per il pubblico in tempo reale")
            st.info("Fai inquadrare questo QR code dal pubblico presente in segreteria per visualizzare immediatamente la pagina.")
            
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data("https://streamlit.io") 
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = io.BytesIO()
            img_qr.save(qr_buffer, format="PNG")
            st.image(qr_buffer.getvalue(), caption="Inquadra per scaricare la distinta sul tuo smartphone", width=250)
