import io
import re
from datetime import datetime

import pandas as pd
import streamlit as st
import pytesseract
import qrcode
from PIL import Image, ImageOps, ImageFilter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

st.set_page_config(page_title="Distinte → PDF pubblico", page_icon="⚽", layout="wide")

st.title("⚽ Distinte giocatori → PDF")
st.write("Carica le distinte, estrai giocatori, anno di nascita e allenatori, correggi i dati e genera il PDF.")

def preprocess(img):
    img = img.convert("L")
    w, h = img.size
    if w < 2200:
        scale = 2200 / w
        img = img.resize((int(w * scale), int(h * scale)))
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img

def ocr(img):
    return pytesseract.image_to_string(
        preprocess(img),
        lang="ita+eng",
        config="--psm 6"
    )

def clean(s):
    return re.sub(r"\s+", " ", str(s)).strip()

def detect_team(text):
    patterns = [
        r"\d+\s+([A-ZÀ-ÖØ-Ý0-9 .'\-&]+)\s*\n",
        r"Distinta.*?\n.*?\n.*?-\s*([A-ZÀ-ÖØ-Ý0-9 .'\-&]+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I | re.S)
        if m:
            candidate = clean(m.group(1))
            if len(candidate) > 4 and "FIGC" not in candidate and "LEGA" not in candidate:
                return candidate
    return ""

def year_from_date(date):
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", date)
    return m.group(3)[-2:] if m else ""

def extract_players(text):
    players = []

    # Modello FIGC: "1 19/08/2004 CHERUBIN LUCA ..."
    p1 = re.compile(
        r"^\s*\d+\s+(\d{2}/\d{2}/\d{4})\s+([A-ZÀ-ÖØ-Ý][A-ZÀ-ÖØ-Ý .'\-]+?)(?=\s{2,}\d{5,}|\s+C\s+\d|\s+V\s+\d|$)",
        re.I
    )
    for line in text.splitlines():
        line = clean(line)
        m = p1.match(line)
        if m:
            name = clean(m.group(2))
            # evita intestazioni e righe non giocatore
            if len(name) >= 4 and not any(x in name.upper() for x in ["COGNOME", "DOCUMENTO", "DISTINTA"]):
                players.append({"Nome": name.upper(), "Anno": year_from_date(m.group(1))})

    # Modello con G M A: "1 26 06 '05 VENTURINI Leonardo ..."
    p2 = re.compile(
        r"^\s*\d+\s+\d{1,2}\s+\d{1,2}\s+[’']?(\d{2})\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ .'\-]+?)(?=\s{2,}|$)"
    )
    for line in text.splitlines():
        line = clean(line)
        m = p2.match(line)
        if m:
            name = clean(m.group(2))
            if len(name) >= 4:
                players.append({"Nome": name.upper(), "Anno": m.group(1)})

    # fallback: righe numerate nella parte della distinta
    if not players:
        for line in text.splitlines():
            line = clean(line)
            m = re.match(r"^(\d{1,2})\s+(.+)$", line)
            if m:
                rest = m.group(2)
                if re.search(r"\b(19|20)\d{2}\b", rest):
                    continue
                if any(k in rest.upper() for k in ["ASSISTENTE", "ALLENATORE", "DIRIGENTE", "MEDICO"]):
                    continue

    # deduplica
    out, seen = [], set()
    for p in players:
        key = p["Nome"].casefold()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def extract_coaches(text):
    coaches = []
    patterns = [
        r"Allenatore(?:\s+Sig\.)?\s*[:\-]?\s*([A-ZÀ-ÖØ-Ý][A-ZÀ-ÖØ-Ý .'\-]+)",
        r"Allenatore in seconda(?:\s+Sig\.)?\s*[:\-]?\s*([A-ZÀ-ÖØ-Ý][A-ZÀ-ÖØ-Ý .'\-]+)",
    ]
    for p in patterns:
        for m in re.finditer(p, text, re.I):
            name = clean(m.group(1))
            name = re.split(r"\s{2,}|\bTessera\b|\bMatricola\b", name, flags=re.I)[0].strip()
            if len(name) >= 4:
                coaches.append(name.upper())
    return list(dict.fromkeys(coaches))

def make_pdf(teams):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontSize=20, leading=24, spaceAfter=10)
    team_style = ParagraphStyle("team", parent=styles["Heading1"], fontSize=16, leading=20, spaceAfter=8)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=9, leading=11)

    story = [Paragraph("DISTINTE GIOCATORI", title)]
    for idx, team in enumerate(teams):
        if idx:
            story.append(PageBreak())
        story.append(Paragraph(team["team"] or "Squadra", team_style))
        story.append(Spacer(1, 3*mm))

        data = [["#", "Giocatore", "Anno"]]
        for i, p in enumerate(team["players"], 1):
            data.append([str(i), p["Nome"], "'" + p["Anno"] if p["Anno"] else ""])

        table = Table(data, colWidths=[12*mm, 125*mm, 25*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#222222")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 10),
            ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f2f2")]),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("RIGHTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(table)

        if team["coaches"]:
            story.append(Spacer(1, 7*mm))
            story.append(Paragraph("<b>Allenatori</b>", styles["Heading3"]))
            for c in team["coaches"]:
                story.append(Paragraph(c, small))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

if "teams" not in st.session_state:
    st.session_state.teams = []

files = st.file_uploader(
    "Carica una o più distinte JPG/PNG",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if files and st.button("🔎 Estrai squadre, giocatori, anni e allenatori", type="primary"):
    teams = []
    with st.spinner("Analizzo le distinte..."):
        for f in files:
            img = Image.open(f)
            text = ocr(img)
            teams.append({
                "team": detect_team(text),
                "players": extract_players(text),
                "coaches": extract_coaches(text),
                "file": f.name,
                "raw": text
            })
    st.session_state.teams = teams

if st.session_state.teams:
    st.divider()
    st.subheader("✏️ Dati estratti e modificabili")

    edited_teams = []
    for ti, team in enumerate(st.session_state.teams):
        st.markdown(f"### {team['file']}")
        team_name = st.text_input("Nome squadra", team["team"], key=f"team_{ti}")

        df = pd.DataFrame(team["players"], columns=["Nome", "Anno"])
        if df.empty:
            df = pd.DataFrame([{"Nome": "", "Anno": ""}])

        edited = st.data_editor(
            df, num_rows="dynamic", hide_index=True,
            use_container_width=True, key=f"players_{ti}",
            column_config={
                "Nome": st.column_config.TextColumn("Giocatore"),
                "Anno": st.column_config.TextColumn("Anno nascita (es. 05)")
            }
        )

        coaches_default = "\n".join(team["coaches"])
        coaches = st.text_area(
            "Allenatori (uno per riga)",
            coaches_default,
            key=f"coaches_{ti}"
        )

        players = []
        for _, row in edited.iterrows():
            name = clean(row.get("Nome", ""))
            year = clean(row.get("Anno", ""))
            if name:
                players.append({"Nome": name.upper(), "Anno": year.replace("'", "")})

        edited_teams.append({
            "team": team_name,
            "players": players,
            "coaches": [clean(x).upper() for x in coaches.splitlines() if clean(x)]
        })

    st.session_state.teams = edited_teams

    pdf = make_pdf(st.session_state.teams)

    st.divider()
    st.subheader("📄 PDF")

    st.download_button(
        "⬇️ Scarica PDF",
        pdf,
        file_name="distinte_giocatori.pdf",
        mime="application/pdf",
        type="primary"
    )

    st.subheader("🔗 QR Code per gli spettatori")
    st.write(
        "Per rendere il PDF realmente raggiungibile dagli spettatori, il PDF deve essere "
        "pubblicato su un indirizzo web pubblico. Inserisci qui l'URL pubblico del PDF "
        "oppure, in una fase successiva, collegheremo direttamente un servizio di storage."
    )
    public_url = st.text_input(
        "URL pubblico del PDF",
        placeholder="https://..."
    )

    if public_url:
        qr = qrcode.make(public_url)
        qr_buf = io.BytesIO()
        qr.save(qr_buf, format="PNG")
        st.image(qr_buf.getvalue(), width=260)
        st.download_button(
            "⬇️ Scarica QR Code",
            qr_buf.getvalue(),
            file_name="qr_distinte.png",
            mime="image/png"
        )
