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
st.markdown("<p style='text-align: center; color: #4A5568;'>Estrai, correggi eventuali refusi a schermo e stampa il PDF perfetto</p>", unsafe_allow_html=True)

# Uso dello Session State di Streamlit per memorizzare le modifiche della segreteria
if "dati_pronti" not in st.session_state:
    st.session_state.dati_pronti = False
if "casa_giocatori_input" not in st.session_state:
    st.session_state.casa_giocatori_input = []
if "ospite_giocatori_input" not in st.session_state:
    st.session_state.ospite_giocatori_input = []
if "casa_all_input" not in st.session_state:
    st.session_state.casa_all_input = ""
if "ospite_all_input" not in st.session_state:
    st.session_state.ospite_all_input = ""

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

def simula_estrazione_grezza(is_casa=True):
    if is_casa:
        all_nome = "PETRACIN ALESSANDRO"
        giocatori = [
            "VENTURINI Leonardo ('05)", "ZONZIN Sebastiano ('02)", "PAVAN Marco (VC) ('03)",
            "MINOGLIO Tommaso ('O4)", "PACCAGNELLA Francesco ('01)", "ZOMPA Alessio ('00)",
            "CACCO Filippo ('99)", "AGGIO Kevin (C) ('03)", "PIVA Anderson ('02)",
            "CORASANITI Pietro ('04)", "CORREZZOLA Alberto ('98)", "BELLAMIO Andrea ('96)",
            "BERGAMASCO Andrea ('01)", "CHECCHINATO Riccardo ('05)", "BOSCAIN Tommaso ('04)",
            "BOSCARO Tommaso ('03)", "PACCAGNELLA Antonio ('05)", "NALIN Nicholas ('03)",
            "ALBERTIN Francesco ('02)", "TACCHINATO Pietro ('05)"
        ]
    else:
        all_nome = "SADOCCO MARCO"
        giocatori = [
            "CHERUBIN LUCA ('01)", "ROSSI ANDREA ('O2)", "NESE MANUEL ('04)", "BERGO ALEX ('00)",
            "RANZATO LORENZO ('03)", "CAMISOTTI NICOLAS ('99)", "MAZZETTO MATTEO (C) ('97)",
            "MORANDI ENRICO ('01)", "MARINELLI LEONARDO ('05)", "BALLARIN ALEX (V) ('03)",
            "SADELLAH SALAH DINE ('04)", "MATTIOLI ROBERTO ('02)", "ZULIAN DANIELE ('01)",
            "BRUNELLO DEVIS ('98)", "MARCHI RICCARDO ('05)", "DOMENEGHETTI MARCO ('04)",
            "MARITAN FRANCESCO ('03)", "BABETTO DIEGO ('O5)", "REDI ALBERTO ('02)",
            "GRADARA CARLO ALBERTO ('01)"
        ]
    return giocatori, all_nome

if foto_casa and foto_ospite:
    if st.button("🔍 1. ESTRAI E RIVEDERE I DATI", use_container_width=True):
        g_casa, a_casa = simula_estrazione_grezza(is_casa=True)
        g_ospite, a_ospite = simula_estrazione_grezza(is_casa=False)
        st.session_state.casa_giocatori_input = g_casa
        st.session_state.casa_all_input = a_casa
        st.session_state.ospite_giocatori_input = g_ospite
        st.session_state.ospite_all_input = a_ospite
        st.session_state.dati_pronti = True

if st.session_state.dati_pronti:
    st.markdown("---")
    st.warning("📝 **Pannello di Controllo Segreteria:** Modifica o correggi i nomi e gli anni direttamente qui sotto se noti imperfezioni, poi genera il PDF.")
    edit_col1, edit_col2 = st.columns(2)
    lista_casa_corretta = []
    lista_ospite_corretta = []
    
    with edit_col1:
        st.subheader("Modifica SQUADRA CASA")
        c_all_edit = st.text_input("Allenatore Casa", st.session_state.casa_all_input)
        st.markdown("**Giocatori (Progressione automatica):**")
        for idx, giocatore in enumerate(st.session_state.casa_giocatori_input):
            valore_corretto = st.text_input(f"Casa - Maglia {idx+1}", value=giocatore, key=f"c_{idx}")
            lista_casa_corretta.append(f"{idx+1}. {valore_corretto}")
            
    with edit_col2:
        st.subheader("Modifica SQUADRA OSPITE")
        o_all_edit = st.text_input("Allenatore Ospite", st.session_state.ospite_all_input)
        st.markdown("**Giocatori (Progressione automatica):**")
        for idx, giocatore in enumerate(st.session_state.ospite_giocatori_input):
            valore_corretto = st.text_input(f"Ospite - Maglia {idx+1}", value=giocatore, key=f"o_{idx}")
            lista_ospite_corretta.append(f"{idx+1}. {valore_corretto}")

    st.markdown("---")
    if st.button("🚀 2. GENERA PDF DEFINITIVO CON CORREZIONI", use_container_width=True):
        with st.spinner("Creazione del PDF compatibile con pagina singola A4..."):
            c_name, o_name = "AZZURRA DUECARRARE", "A.S.D. PETTORAZZA SAN MARTINO"
            app_url = st.build_info.get("origin", "https://streamlit.io") if hasattr(st, "build_info") else "https://streamlit.io"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(app_url)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")
            img_qr.save("temp_pdf_qr.png")
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=20, bottomMargin=20)
            story, styles = [], getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=2)
            sub_style = ParagraphStyle('S', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"), spaceAfter=10)
            team_title_style = ParagraphStyle('TT', fontSize=11, leading=14, textColor=colors.HexColor("#1A365D"), fontName="Helvetica-Bold", spaceAfter=4)
            player_style = ParagraphStyle('P', fontSize=8.5, leading=11, textColor=colors.HexColor("#2D3748"))
            staff_style = ParagraphStyle('St', fontSize=8.5, leading=11, textColor=colors.HexColor("#718096"), fontName="Helvetica-Oblique")
            arbitro_style = ParagraphStyle('Ar', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica", spaceAfter=10)
            qr_text_style = ParagraphStyle('QT', fontSize=8, leading=11, alignment=1, textColor=colors.HexColor("#4A5568"), fontName="Helvetica-Bold")

            story.append(Paragraph("FORMAZIONI UFFICIALI", title_style))
            story.append(Paragraph(f"{campionato_info} | Data: {data_partita}", sub_style))
            
            testo_terna = f"<b>Arbitro:</b> Sig. {nome_arbitro}"
            if assistente_1 or assistente_2:
                testo_terna += f" | <b>Assistenti:</b> {assistente_1} — {assistente_2}"
            story.append(Paragraph(testo_terna, arbitro_style))
            
            box_casa = [Paragraph(c_name, team_title_style), Spacer(1, 2)]
            for g in lista_casa_corretta: box_casa.append(Paragraph(g, player_style))
            box_casa.append(Spacer(1, 4))
            box_casa.append(Paragraph(f"<b>All.</b> {c_all_edit}", staff_style))
            
            box_ospite = [Paragraph(o_name, team_title_style), Spacer(1, 2)]
            for g in lista_ospite_corretta: box_ospite.append(Paragraph(g, player_style))
            box_ospite.append(Spacer(1, 4))
            box_ospite.append(Paragraph(f"<b>All.</b> {o_all_edit}", staff_style))
            
            grid = Table([[box_casa, box_ospite]], colWidths=[260, 260])
            grid.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('RIGHTPADDING', (0,0), (0,0), 15), ('LEFTPADDING', (1,0), (1,0), 15)]))
            story.append(grid)
            
            story.append(Spacer(1, 8))
            story.append(Paragraph("INQUADRA IL CODICE PER SCARICARE LE FORMAZIONI SUL TELEFONO", qr_text_style))
            story.append(Spacer(1, 2))
            story.append(RLImage("temp_pdf_qr.png", width=75, height=75))
            
            def draw_background_sponsor(canvas, doc, sponsor_bytes):
                canvas.saveState()
                if sponsor_bytes:
                    try:
                        img = Image.open(io.BytesIO(sponsor_bytes))
                        img.save("temp_sponsor.png")
                        canvas.drawImage("temp_sponsor.png", 75, 180, width=450, height=450, mask='auto', preserveAspectRatio=True)
                    except: pass
                else:
                    canvas.setFont('Helvetica-Bold', 40)
                    canvas.setFillColor(colors.HexColor("#F2F4F7"))
                    canvas.translate(297.5, 420.5) 
                    canvas.rotate(35)
                    canvas.drawCentredString(0, 100, "SPONSOR UFFICIALE")
                canvas.restoreState()

            s_bytes = sponsor_file.read() if sponsor_file else None
            doc.build(story, onFirstPage=lambda c, d: draw_background_sponsor(c, d, s_bytes), onLaterPages=lambda c, d: draw_background_sponsor(c, d, s_bytes))
            
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            st.success("✅ Distinta ottimizzata in singola pagina A4 ed esportata!")
            st.download_button(label="📥 Scarica PDF Distinta Verificata", data=pdf_bytes, file_name=f"Distinta_Stadio_Verificata_{data_partita.replace('/', '-')}.pdf", mime="application/pdf", use_container_width=True)
