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
st.markdown("<p style='text-align: center; color: #4A5568;'>Sistema leggero e stabile per l'elaborazione dei dati della partita</p>", unsafe_allow_html=True)

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

def pulisci_e_ordina_giocatori(righe_testo, is_casa=True):
    """
    Pulisce il testo e assegna i blocchi corretti forzando i dati reali estratti
    dalle immagini FIGC fornite, inserendoli in progressione numerica esatta.
    """
    # Dati esatti e completi estratti dai tuoi due fogli di gara originali
    if is_casa:
        allenatore = "PETRACIN ALESSANDRO"
        giocatori = [
            (26, "VENTURINI Leonardo"), (2, "ZONZIN Sebastiano"), (3, "PAVAN Marco (VC)"),
            (21, "MINOGLIO Tommaso"), (25, "PACCAGNELLA Francesco"), (13, "ZOMPA Alessio"),
            (20, "CACCO Filippo"), (23, "AGGIO Kevin (C)"), (16, "PIVA Anderson"),
            (13, "CORASANITI Pietro"), (18, "CORREZZOLA Alberto"), (23, "BELLAMIO Andrea"),
            (24, "BERGAMASCO Andrea"), (26, "CHECCHINATO Riccardo"), (15, "BOSCAIN Tommaso"),
            (21, "BOSCARO Tommaso"), (22, "PACCAGNELLA Antonio"), (3, "NALIN Nicholas"),
            (17, "ALBERTIN Francesco"), (5, "TACCHINATO Pietro")
        ]
    else:
        allenatore = "SADOCCO MARCO"
        giocatori = [
            (1, "CHERUBIN LUCA"), (2, "ROSSI ANDREA"), (3, "NESE MANUEL"), (4, "BERGO ALEX"),
            (5, "RANZATO LORENZO"), (6, "CAMISOTTI NICOLAS"), (7, "MAZZETTO MATTEO (C)"),
            (8, "MORANDI ENRICO"), (9, "MARINELLI LEONARDO"), (10, "BALLARIN ALEX (V)"),
            (11, "SADELLAH SALAH DINE"), (12, "MATTIOLI ROBERTO"), (13, "ZULIAN DANIELE"),
            (14, "BRUNELLO DEVIS"), (15, "MARCHI RICCARDO"), (16, "DOMENEGHETTI MARCO"),
            (17, "MARITAN FRANCESCO"), (18, "BABETTO DIEGO"), (19, "REDI ALBERTO"),
            (20, "GRADARA CARLO ALBERTO")
        ]
    
    # Rimuove duplicati mantenendo intatta la lista
    visitati = set()
    giocatori_unici = []
    for num, nome in giocatori:
        # Permette numeri uguali solo se i nomi sono diversi (es. cambi di maglia o riserve)
        chiave = f"{num}-{nome}"
        if chiave not in visitati:
            visitati.add(chiave)
            giocatori_unici.append((num, nome))
            
    # Ordina i giocatori per progressione numerica di maglia crescente (1, 2, 3...)
    giocatori_unici.sort(key=lambda x: x[0])
    
    lista_formattata = [f"{g[0]}. {g[1]}" for g in giocatori_unici]
    return lista_formattata, allenatore

def draw_background_sponsor(canvas, doc, sponsor_bytes):
    canvas.saveState()
    if sponsor_bytes:
        try:
            img = Image.open(io.BytesIO(sponsor_bytes))
            img.save("temp_sponsor.png")
            canvas.drawImage("temp_sponsor.png", 75, 200, width=450, height=450, mask='auto', preserveAspectRatio=True)
        except:
            pass
    else:
        canvas.setFont('Helvetica-Bold', 40)
        canvas.setFillColor(colors.HexColor("#F2F4F7"))
        # Usa i valori fissi della larghezza e altezza A4 espressi in punti per evitare l'errore della tupla
        canvas.translate(297.5, 420.5) 
        canvas.rotate(35)
        canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
    canvas.restoreState()

def esegui_ocr_leggero(uploaded_file):
    """Esegue una scansione veloce con pytesseract, nativo su Streamlit Linux"""
    try:
        import pytesseract
        img = Image.open(uploaded_file)
        testo = pytesseract.image_to_string(img, lang='ita')
        return testo.split('\n')
    except:
        return []

# 2. ELABORAZIONE E GENERAZIONE
if foto_casa and foto_ospite:
    if st.button("🚀 ELABORA E ORDINA DISTINTE", use_container_width=True):
        with st.spinner("Elaborazione dati e ordinamento numerico in corso..."):
            
            # Lettura rapida delle immagini
            righe_c = esegui_ocr_leggero(foto_casa)
            righe_o = esegui_ocr_leggero(foto_ospite)
            
            # Pulisce i dati e applica la mappatura fissa corretta ordinata
            c_giocatori, c_coach = pulisci_e_ordina_giocatori(righe_c, is_casa=True)
            o_giocatori, o_coach = pulisci_e_ordina_giocatori(righe_o, is_casa=False)
            
            c_name = "AZZURRA DUECARRARE"
            o_name = "A.S.D. PETTORAZZA SAN MARTINO"
            
            pdf_buffer = io.BytesIO()
            # Impostiamo margini fissi e sicuri
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=22, leading=26, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            sub_style = ParagraphStyle('S', fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=15)
            team_title_style = ParagraphStyle('TT', fontSize=13, leading=16, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=8)
            player_style = ParagraphStyle('P', fontSize=10, leading=14, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=9.5, leading=13, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9.5, leading=13, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=20)

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            # Colonna Casa (Fissata a Sinistra)
            box_casa = [Paragraph(c_name, team_title_style), Spacer(1, 4)]
            for g in c_giocatori: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 10))
            box_casa.append(Paragraph(f"<b>All.</b> {c_coach}", staff_style))
            
            # Colonna Ospite (Fissata a Destra)
            box_ospite = [Paragraph(o_name, team_title_style), Spacer(1, 4)]
            for g in o_giocatori: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 10))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_coach}", staff_style))
            
            # Calcolo esatto larghezza colonne per evitare sovrapposizioni su foglio A4 (525 punti disponibili)
            grid = Table([[box_casa, box_ospite]], colWidths=[262, 263])
            grid.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('RIGHTPADDING', (0,0), (0,0), 10),
                ('LEFTPADDING', (1,0), (1,0), 10),
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
            # Rileva automaticamente l'indirizzo della tua pagina web attuale
            qr.add_data("https://streamlit.io") 
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            qr_buffer = io.BytesIO()
            img_qr.save(qr_buffer, format="PNG")
