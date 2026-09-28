import streamlit as st
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# Configurazione grafica della pagina web
st.set_page_config(page_title="Generatore Distinte Gara", page_icon="⚽", layout="centered")

st.markdown("<h1 style='text-align: center; color: #1A365D;'>⚽ GESTIONE DISTINTE STADIO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4A5568;'>Carica le foto delle due distinte ufficiali per generare il PDF per il pubblico</p>", unsafe_allow_html=True)

# 1. SIDEBAR: CONFIGURAZIONE ED ELEMENTI FISSI
st.sidebar.header("⚙️ Configurazione Partita")
sponsor_file = st.sidebar.file_uploader("Carica Logo Sponsor (PNG)", type=["png", "jpg", "jpeg"])
data_partita = st.sidebar.text_input("Data della partita", "28/09/2026")
campionato_info = st.sidebar.text_input("Campionato / Girone", "1° Categoria - Girone E")

st.sidebar.header("⚖️ Terna Arbitrale")
nome_arbitro = st.sidebar.text_input("Arbitro (Sig.)", "Rossi di Verona")
assistente_1 = st.sidebar.text_input("Assistente 1", "Bianchi di Padova")
assistente_2 = st.sidebar.text_input("Assistente 2", "Verdi di Rovigo")

st.subheader("📸 Carica le immagini delle squadre")
col1, col2 = st.columns(2)

with col1:
    foto_casa = st.file_uploader("Distinta Squadra CASA", type=["png", "jpg", "jpeg"])
with col2:
    foto_ospite = st.file_uploader("Distinta Squadra OSPITE", type=["png", "jpg", "jpeg"])

# Funzione per disegnare lo sponsor sullo sfondo del PDF
def draw_background_sponsor(canvas, doc, sponsor_bytes):
    canvas.saveState()
    if sponsor_bytes:
        from PIL import Image
        img = Image.open(io.BytesIO(sponsor_bytes))
        img.save("temp_sponsor.png")
        canvas.drawImage("temp_sponsor.png", 75, 200, width=450, height=450, mask='auto', preserveAspectRatio=True)
    else:
        canvas.setFont('Helvetica-Bold', 40)
        canvas.setFillColor(colors.HexColor("#F2F4F7"))
        canvas.translate(A4/2, A4/2)
        canvas.rotate(35)
        canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
    canvas.restoreState()

# Mappatura dati reali estratti dai tuoi file di esempio
def estrai_dati_mock(file_name, is_casa=True):
    if is_casa:
        return "AZZURRA DUECARRARE", [
            "26. VENTURINI Leonardo", "2. ZONZIN Sebastiano", "3. PAVAN Marco (VC)",
            "21. MINOGLIO Tommaso", "25. PACCAGNELLA Francesco", "13. ZOMPA Alessio",
            "20. CACCO Filippo", "23. AGGIO Kevin (C)", "16. PIVA Anderson",
            "13. CORASANITI Pietro", "18. CORREZZOLA Alberto", "23. BELLAMIO Andrea",
            "24. BERGAMASCO Andrea", "26. CHECCHINATO Riccardo", "15. BOSCAIN Tommaso"
        ], "PETRACIN ALESSANDRO"
    else:
        return "A.S.D. PETTORAZZA SAN MARTINO", [
            "1. CHERUBIN LUCA", "2. ROSSI ANDREA", "3. NESE MANUEL", "4. BERGO ALEX",
            "5. RANZATO LORENZO", "6. CAMISOTTI NICOLAS", "7. MAZZETTO MATTEO (C)",
            "8. MORANDI ENRICO", "9. MARINELLI LEONARDO", "10. BALLARIN ALEX (V)",
            "11. SADELLAH SALAH DINE", "12. MATTIOLI ROBERTO"
        ], "SADOCCO MARCO"

# 2. ELABORAZIONE E GENERAZIONE DEL PDF
if foto_casa and foto_ospite:
    if st.button("🚀 ELABORA E CREA PDF", use_container_width=True):
        with st.spinner("Generazione PDF in corso..."):
            
            c_name, c_players, c_coach = estrai_dati_mock(foto_casa.name, is_casa=True)
            o_name, o_players, o_coach = estrai_dati_mock(foto_ospite.name, is_casa=False)
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
            story = []
            styles = getSampleStyleSheet()
            
            # Stili grafici
            title_style = ParagraphStyle('T', fontSize=22, leading=26, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            sub_style = ParagraphStyle('S', fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=15)
            team_title_style = ParagraphStyle('TT', fontSize=13, leading=16, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=8)
            player_style = ParagraphStyle('P', fontSize=11, leading=15, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=10, leading=14, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9.5, leading=13, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=20)

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            # Sezione Arbitro e Assistenti sotto il titolo
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            # Colonna Casa
            box_casa = [Paragraph(c_name, team_title_style), Spacer(1, 4)]
            for g in c_players: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 10))
            box_casa.append(Paragraph(f"<b>All.</b> {c_coach}", staff_style))
            
            # Colonna Ospite
            box_ospite = [Paragraph(o_name, team_title_style), Spacer(1, 4)]
            for g in o_players: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 10))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_coach}", staff_style))
            
            # Tabella affiancata
            grid = Table([[box_casa, box_ospite]], colWidths=[260, 260])
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
            
            st.success("✅ PDF Generato con successo!")
            
            st.download_button(
                label="📥 Scarica PDF della Partita con Terna Arbitrale",
                data=pdf_bytes,
                file_name=f"Formazioni_{data_partita.replace('/', '-')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
