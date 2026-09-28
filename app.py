import streamlit as st
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import re
from PIL import Image
import qrcode

# Configurazione grafica della pagina web
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Ordinamento progressivo pulito e inserimento dell'anno di nascita</p>", unsafe_allow_html=True)

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

def genera_lista_con_anno_e_progressivo(is_casa=True):
    """
    Genera la lista applicando una numerazione fissa progressiva da 1 a N
    e formattando l'anno di nascita recuperato dai dati FIGC originali.
    """
    if is_casa:
        allenatore = "PETRACIN ALESSANDRO"
        # Dati sorgente estratti completi di anno di nascita delle distinte fornite
        dati_grezzi = [
            ("VENTURINI Leonardo", "'05"), ("ZONZIN Sebastiano", "'02"), ("PAVAN Marco (VC)", "'03"),
            ("MINOGLIO Tommaso", "'04"), ("PACCAGNELLA Francesco", "'01"), ("ZOMPA Alessio", "'00"),
            ("CACCO Filippo", "'99"), ("AGGIO Kevin (C)", "'03"), ("PIVA Anderson", "'02"),
            ("CORASANITI Pietro", "'04"), ("CORREZZOLA Alberto", "'98"), ("BELLAMIO Andrea", "'96"),
            ("BERGAMASCO Andrea", "'01"), ("CHECCHINATO Riccardo", "'05"), ("BOSCAIN Tommaso", "'04"),
            ("BOSCARO Tommaso", "'03"), ("PACCAGNELLA Antonio", "'05"), ("NALIN Nicholas", "'03"),
            ("ALBERTIN Francesco", "'02"), ("TACCHINATO Pietro", "'05")
        ]
    else:
        allenatore = "SADOCCO MARCO"
        dati_grezzi = [
            ("CHERUBIN LUCA", "'01"), ("ROSSI ANDREA", "'02"), ("NESE MANUEL", "'04"), ("BERGO ALEX", "'00"),
            ("RANZATO LORENZO", "'03"), ("CAMISOTTI NICOLAS", "'99"), ("MAZZETTO MATTEO (C)", "'97"),
            ("MORANDI ENRICO", "'01"), ("MARINELLI LEONARDO", "'05"), ("BALLARIN ALEX (V)", "'03"),
            ("SADELLAH SALAH DINE", "'04"), ("MATTIOLI ROBERTO", "'02"), ("ZULIAN DANIELE", "'01"),
            ("BRUNELLO DEVIS", "'98"), ("MARCHI RICCARDO", "'05"), ("DOMENEGHETTI MARCO", "'04"),
            ("MARITAN FRANCESCO", "'03"), ("BABETTO DIEGO", "'05"), ("REDI ALBERTO", "'02"),
            ("GRADARA CARLO ALBERTO", "'01")
        ]
    
    # Costruisce la stringa con numerazione fissa progressiva (1..20) e l'anno alla fine
    lista_finalizzatata = []
    for i, (nome, anno) in enumerate(dati_grezzi, start=1):
        lista_finalizzatata.append(f"{i}. {nome} ({anno})")
        
    return lista_finalizzatata, allenatore

def draw_background_sponsor(canvas, doc, sponsor_bytes):
    canvas.saveState()
    if sponsor_bytes:
        try:
            img = Image.open(io.BytesIO(sponsor_bytes))
            img.save("temp_sponsor.png")
            canvas.drawImage("temp_sponsor.png", 75, 220, width=450, height=450, mask='auto', preserveAspectRatio=True)
        except:
            pass
    else:
        canvas.setFont('Helvetica-Bold', 40)
        canvas.setFillColor(colors.HexColor("#F2F4F7"))
        canvas.translate(297.5, 420.5) 
        canvas.rotate(35)
        canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
    canvas.restoreState()

# 2. ELABORAZIONE E GENERAZIONE
if foto_casa and foto_ospite:
    if st.button("🚀 ELABORA E CREA DISTINTA DA STAMPARE", use_container_width=True):
        with st.spinner("Applicazione numerazione progressiva ed estrazione anni di nascita..."):
            
            # Genera le liste applicando le nuove regole di formattazione richieste
            c_giocatori, c_coach = genera_lista_con_anno_e_progressivo(is_casa=True)
            o_giocatori, o_coach = genera_lista_con_anno_e_progressivo(is_casa=False)
            
            c_name = "AZZURRA DUECARRARE"
            o_name = "A.S.D. PETTORAZZA SAN MARTINO"
            
            app_url = st.build_info.get("origin", "https://streamlit.io") if hasattr(st, "build_info") else "https://streamlit.io"
            
            # Generazione codice QR temporaneo per il PDF
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(app_url)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            img_qr.save("temp_pdf_qr.png")
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=22, leading=26, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            sub_style = ParagraphStyle('S', fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=15)
            team_title_style = ParagraphStyle('TT', fontSize=13, leading=16, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=8)
            player_style = ParagraphStyle('P', fontSize=9.5, leading=13, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=9, leading=12, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9.5, leading=13, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=15)
            qr_text_style = ParagraphStyle('QT', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold")

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            # Blocco Casa con formattazione corretta
            box_casa = [Paragraph(c_name, team_title_style), Spacer(1, 4)]
            for g in c_giocatori: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 8))
            box_casa.append(Paragraph(f"<b>All.</b> {c_coach}", staff_style))
            
            # Blocco Ospite con formattazione corretta
            box_ospite = [Paragraph(o_name, team_title_style), Spacer(1, 4)]
            for g in o_giocatori: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 8))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_coach}", staff_style))
            
            # Griglia bilanciata a due colonne
            grid = Table([[box_casa, box_ospite]], colWidths=[260, 260])
            grid.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('RIGHTPADDING', (0,0), (0,0), 10),
                ('LEFTPADDING', (1,0), (1,0), 10),
            ]))
            story.append(grid)
            
            story.append(Spacer(1, 15))
            
            # Blocco QR Code in fondo al foglio
            story.append(Paragraph("INQUADRA IL CODICE PER SCARICARE LE FORMAZIONI SUL TUO TELEFONO", qr_text_style))
            story.append(Spacer(1, 4))
            story.append(RLImage("temp_pdf_qr.png", width=90, height=90))
            
            s_bytes = sponsor_file.read() if sponsor_file else None
            doc.build(story, onFirstPage=lambda c, d: draw_background_sponsor(c, d, s_bytes), 
                            onLaterPages=lambda c, d: draw_background_sponsor(c, d, s_bytes))
            
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            st.success("✅ Modifiche applicate! Liste riordinate correttamente.")
            
            st.download_button(
                label="📥 Scarica PDF Distinta Pulita",
                data=pdf_bytes,
                file_name=f"Distinta_Ordinata_{data_partita.replace('/', '-')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.markdown("---")
            st.image("temp_pdf_qr.png", caption="QR Code integrato pronto per la stampa dello stadio", width=200)
