import io
import re
from pathlib import Path

import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

st.set_page_config(page_title="Distinte partita", page_icon="⚽", layout="wide")

st.title("⚽ Distinte partita → PDF A4")
st.caption("Due distinte, squadra di casa e squadra ospite, su un unico foglio A4.")

# ------------------------------------------------------------
# OCR
# ------------------------------------------------------------

def prep(img):
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.resize((img.width * 3, img.height * 3))
    return img

def remove_grid_lines(img):
    """Riduce le linee della tabella per aiutare l'OCR."""
    import cv2
    import numpy as np

    arr = np.array(img)
    bw = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    horizontal = cv2.morphologyEx(
        bw, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1))
    )
    vertical = cv2.morphologyEx(
        bw, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, 45))
    )

    lines = cv2.bitwise_or(horizontal, vertical)
    cleaned = cv2.subtract(bw, lines)
    cleaned = cv2.bitwise_not(cleaned)

    return Image.fromarray(cleaned)

def ocr_crop(img, box, psm=6):
    crop = img.crop(box)
    crop = prep(crop)
    crop = remove_grid_lines(crop)
    return pytesseract.image_to_string(
        crop,
        lang="ita+eng",
        config=f"--psm {psm}",
        timeout=30
    )

def normalize_name(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^[^A-Za-zÀ-ÖØ-öø-ÿ]+", "", s)
    s = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ .'\-]+$", "", s)
    return s.strip()

def is_name(s):
    letters = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]", s)
    if len(letters) < 4:
        return False
    bad = [
        "cognome", "nome", "stadio", "campo", "matricola",
        "documento", "identificazione", "allenatore", "dirigente",
        "assistente", "medico", "tessera", "comune"
    ]
    return not any(x in s.lower() for x in bad)

def extract_names_from_lines(text):
    result = []
    for line in text.splitlines():
        n = normalize_name(line)
        if is_name(n):
            result.append(n.upper())

    # deduplica conservando ordine
    out = []
    seen = set()
    for n in result:
        k = re.sub(r"[^a-zà-öø-ÿ]", "", n.lower())
        if k and k not in seen:
            seen.add(k)
            out.append(n)
    return out

def extract_team_name(img, model):
    # Il nome viene lasciato facilmente correggibile dall'utente.
    if model == "figc":
        crop = img.crop((250, 50, img.width - 40, 230))
    else:
        crop = img.crop((250, 30, img.width - 40, 220))

    text = pytesseract.image_to_string(
        prep(crop), lang="ita+eng", config="--psm 6", timeout=30
    )

    # Pattern FIGC: "915577 A.S.D. PETTORAZZA SAN MARTINO"
    m = re.search(
        r"\b\d{5,7}\s+(.+?)(?:\n|$)",
        text,
        re.I
    )
    if m:
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        if name:
            return name.upper()

    # fallback: prima riga significativa
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) > 4 and "FIGC" not in line.upper():
            return line.upper()

    return ""

def extract_figc(img):
    # Prima distinta dell'esempio:
    # colonna Cognome e nome circa x 19%-42%, tabella circa y 21%-75%.
    w, h = img.size
    name_box = (int(w*.175), int(h*.205), int(w*.445), int(h*.745))
    year_box = (int(w*.085), int(h*.205), int(w*.175), int(h*.745))

    names_text = ocr_crop(img, name_box, 6)
    year_text = ocr_crop(img, year_box, 6)

    names = extract_names_from_lines(names_text)

    # Anni: ricaviamo gli anni dalle date riconosciute.
    dates = re.findall(r"\b\d{1,2}[\/\-]\d{1,2}[\/\-](\d{4})\b", year_text)
    years = [x[-2:] for x in dates]

    players = []
    for i, name in enumerate(names[:30]):
        players.append({
            "Nome": name,
            "Anno": years[i] if i < len(years) else ""
        })

    # Staff: cerchiamo solo "Allenatore", evitando la sezione giocatori.
    full = pytesseract.image_to_string(
        prep(img), lang="ita+eng", config="--psm 6", timeout=45
    )
    coaches = []
    for m in re.finditer(
        r"Allenatore\s*:?\s*([A-ZÀ-ÖØ-Ý][A-ZÀ-ÖØ-Ý .'\-]+)",
        full, re.I
    ):
        n = normalize_name(m.group(1))
        n = re.split(r"\s{2,}|Tessera|Matricola", n, flags=re.I)[0]
        if is_name(n):
            coaches.append(n.upper())

    return players, list(dict.fromkeys(coaches))

def extract_other(img):
    # Seconda distinta dell'esempio:
    # G/M/A + Cognome e Nome.
    w, h = img.size
    name_box = (int(w*.185), int(h*.265), int(w*.485), int(h*.685))
    birth_box = (int(w*.09), int(h*.265), int(w*.185), int(h*.685))

    names_text = ocr_crop(img, name_box, 6)
    birth_text = ocr_crop(img, birth_box, 6)

    names = extract_names_from_lines(names_text)

    # Cerca gli anni in forme "'05", "05" o "2005".
    years = []
    for line in birth_text.splitlines():
        matches = re.findall(r"(?:['’]\s*)?(\d{2})\b", line)
        # Evita numeri di riga troppo isolati.
        if matches:
            years.append(matches[-1])

    players = []
    for i, name in enumerate(names[:30]):
        players.append({
            "Nome": name,
            "Anno": years[i] if i < len(years) else ""
        })

    full = pytesseract.image_to_string(
        prep(img), lang="ita+eng", config="--psm 6", timeout=45
    )
    coaches = []
    for m in re.finditer(
        r"Allenatore(?:\s+Sig\.)?\s*:?\s*([A-ZÀ-ÖØ-Ý][A-ZÀ-ÖØ-Ý .'\-]+)",
        full, re.I
    ):
        n = normalize_name(m.group(1))
        n = re.split(r"\s{2,}|Tessera|Matricola", n, flags=re.I)[0]
        if is_name(n):
            coaches.append(n.upper())

    return players, list(dict.fromkeys(coaches))

def analyze(file, model):
    img = Image.open(file)
    if model == "figc":
        players, coaches = extract_figc(img)
    else:
        players, coaches = extract_other(img)

    team = extract_team_name(img, model)
    return {
        "team": team,
        "players": players,
        "coaches": coaches,
    }

# ------------------------------------------------------------
# PDF: due squadre su UNA pagina A4, due colonne
# ------------------------------------------------------------

def make_pdf(home, away):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    margin_x = 9 * mm
    top = H - 12 * mm
    gap = 5 * mm
    col_w = (W - 2*margin_x - gap) / 2
    left_x = margin_x
    right_x = margin_x + col_w + gap

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W/2, top, "DISTINTE GIOCATORI")
    c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, top - 5*mm, "Partita")

    def draw_team(x, y, team):
        # cornice colonna
        c.setLineWidth(0.6)
        c.rect(x, 10*mm, col_w, H - 28*mm)

        c.setFont("Helvetica-Bold", 10)
        team_name = team["team"] or "SQUADRA"
        c.drawCentredString(x + col_w/2, y, team_name[:48])
        y -= 6*mm

        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x + 3*mm, y, "#")
        c.drawString(x + 11*mm, y, "GIOCATORE")
        c.drawRightString(x + col_w - 3*mm, y, "ANNO")
        y -= 3*mm
        c.line(x + 2*mm, y, x + col_w - 2*mm, y)
        y -= 4.2*mm

        c.setFont("Helvetica", 7.5)
        for i, p in enumerate(team["players"][:25], 1):
            if y < 29*mm:
                break
            c.drawString(x + 3*mm, y, str(i))
            name = p["Nome"]
            # evita che nomi lunghi escano dalla colonna
            if len(name) > 31:
                name = name[:30] + "…"
            c.drawString(x + 11*mm, y, name)
            year = p.get("Anno", "")
            if year:
                c.drawRightString(x + col_w - 3*mm, y, "'" + year.replace("'", ""))
            y -= 4.5*mm

        y -= 2*mm
        c.line(x + 2*mm, y, x + col_w - 2*mm, y)
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x + 3*mm, y, "ALLENATORI")
        y -= 4.5*mm
        c.setFont("Helvetica", 7.5)
        for coach in team["coaches"][:3]:
            c.drawString(x + 3*mm, y, coach[:40])
            y -= 4.5*mm

    draw_team(left_x, top - 12*mm, home)
    draw_team(right_x, top - 12*mm, away)

    c.setFont("Helvetica", 6.5)
    c.drawCentredString(W/2, 5*mm, "Documento generato automaticamente — verificare i dati prima della pubblicazione.")

    c.save()
    buf.seek(0)
    return buf.getvalue()

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------

st.subheader("1. Carica le due distinte")

c1, c2 = st.columns(2)

with c1:
    st.markdown("### 🏠 Squadra di casa")
    home_file = st.file_uploader(
        "Distinta casa",
        type=["jpg", "jpeg", "png"],
        key="home"
    )
    home_model = st.selectbox(
        "Formato distinta casa",
        ["figc", "standard"],
        format_func=lambda x: "FIGC / Prima distinta" if x == "figc" else "Distinta standard / seconda distinta",
        key="home_model"
    )

with c2:
    st.markdown("### ✈️ Squadra ospite")
    away_file = st.file_uploader(
        "Distinta ospite",
        type=["jpg", "jpeg", "png"],
        key="away"
    )
    away_model = st.selectbox(
        "Formato distinta ospite",
        ["standard", "figc"],
        format_func=lambda x: "Distinta standard / seconda distinta" if x == "standard" else "FIGC / Prima distinta",
        key="away_model"
    )

if st.button("🔎 Estrai dati", type="primary", disabled=not (home_file and away_file)):
    with st.spinner("Analizzo le due distinte..."):
        st.session_state.home_data = analyze(home_file, home_model)
        st.session_state.away_data = analyze(away_file, away_model)

if "home_data" in st.session_state and "away_data" in st.session_state:
    st.divider()
    st.subheader("2. Controlla e correggi i dati")

    for side, label in [("home", "🏠 CASA"), ("away", "✈️ OSPITE")]:
        data = st.session_state[f"{side}_data"]
        st.markdown(f"### {label}")

        data["team"] = st.text_input(
            "Nome squadra",
            data["team"],
            key=f"{side}_team_name"
        )

        df = pd.DataFrame(data["players"])
        if df.empty:
            df = pd.DataFrame(columns=["Nome", "Anno"])

        edited = st.data_editor(
            df,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key=f"{side}_players_editor",
            column_config={
                "Nome": st.column_config.TextColumn("Giocatore"),
                "Anno": st.column_config.TextColumn("Anno nascita", help="Inserire ad esempio 05")
            }
        )

        coaches_text = st.text_area(
            "Allenatori — uno per riga",
            "\n".join(data["coaches"]),
            key=f"{side}_coaches"
        )

        players = []
        for _, row in edited.iterrows():
            name = str(row.get("Nome", "")).strip()
            year = str(row.get("Anno", "")).strip().replace("'", "")
            if name and name.lower() != "nan":
                players.append({"Nome": name.upper(), "Anno": year})

        data["players"] = players
        data["coaches"] = [
            x.strip().upper()
            for x in coaches_text.splitlines()
            if x.strip()
        ]

    st.divider()
    st.subheader("3. Genera il PDF A4")

    pdf = make_pdf(
        st.session_state.home_data,
        st.session_state.away_data
    )

    st.download_button(
        "📄 Scarica PDF — CASA + OSPITE su un solo A4",
        pdf,
        file_name="distinte_partita_A4.pdf",
        mime="application/pdf",
        type="primary"
    )

    st.info(
        "Il PDF è già impaginato in due colonne: squadra di casa a sinistra e squadra ospite a destra. "
        "L'anno di nascita viene mostrato come '05, '04, ecc."
    )
