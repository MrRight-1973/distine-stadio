import base64
import io
import json
import re
from datetime import datetime

from openai import OpenAI
from PIL import Image, ImageOps

MODELLO = "gpt-4o"
VALORI_VUOTI = {"", "N.D.", "ND", "N/A", "NONE", "NULL", "NON INDICATO"}
ETA_MINIMA_GIOCATORE = 5
ANNO_MINIMO = 1940


def pulisci_testo(testo):
    """Rimuove caratteri speciali inutili e standardizza in MAIUSCOLO"""
    if testo is None:
        return ""
    pulito = str(testo).replace("_", " ")
    pulito = re.sub(r"\s+", " ", pulito).strip().upper()
    return "" if pulito in VALORI_VUOTI else pulito


def normalizza_anno(anno_grezzo):
    """Isola l'anno di nascita e lo restituisce nel formato a 4 cifre (YYYY).

    Accetta sia 2 cifre (es. "04") sia 4 cifre. Il range e' coerente per
    entrambi i formati: da ANNO_MINIMO a (anno corrente - ETA_MINIMA_GIOCATORE).
    """
    if anno_grezzo is None:
        return ""
    anno_massimo = datetime.now().year - ETA_MINIMA_GIOCATORE

    # Prende il primo gruppo di cifre lungo 2 o 4 (non unisce gruppi diversi)
    for gruppo in re.findall(r"\d+", str(anno_grezzo)):
        if len(gruppo) == 2:
            anno = 2000 + int(gruppo)
            if anno > anno_massimo:
                anno -= 100
        elif len(gruppo) == 4:
            anno = int(gruppo)
        else:
            continue
        if ANNO_MINIMO <= anno <= anno_massimo:
            return str(anno)
        return ""
    return ""


def _to_int(valore, default=0):
    try:
        return int(str(valore).strip())
    except (ValueError, TypeError):
        return default


def encode_image(uploaded_file):
    """Mantiene alta la risoluzione per l'OCR e corregge l'orientamento EXIF"""
    uploaded_file.seek(0)
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)  # foto da smartphone spesso ruotate nei metadati
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    img.thumbnail((2000, 2000))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=95)
    return base64.b64encode(buffer_img.getvalue()).decode("utf-8")


def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Estrae SOLO l'allenatore, i giocatori e le date per la specifica squadra"""
    if not api_key:
        raise ValueError("Chiave OPENAI_API_KEY non configurata nei secrets.")

    client = OpenAI(api_key=api_key, timeout=90.0, max_retries=2)
    base64_image = encode_image(uploaded_file)

    focus_ruolo = (
        "ATTENZIONE: Stai analizzando la colonna/sezione degli OSPITI. Ignora la squadra di casa."
        if ruolo_squadra == "OSPITE" else
        "ATTENZIONE: Stai analizzando la colonna/sezione dei LOCALI. Ignora la squadra ospite."
    )

    prompt_sistema = (
        f"Sei un sistema OCR ad altissima precisione per distinte LND.\n"
        f"{focus_ruolo}\n\n"
        "REGOLE RIGIDE DI SCANSIONE:\n"
        "1. Trova l'Allenatore della sezione indicata.\n"
        "2. Concentrati sulla colonna dei CALCIATORI e dell'ANNO DI NASCITA riga per riga.\n"
        "3. Cerca la sigla del Capitano (C, CAP) e del Vice (VC, VICE) accanto al nome o al numero.\n\n"
        "Rispondi ESCLUSIVAMENTE con questo schema JSON (NON includere il nome della squadra):\n"
        "{\n"
        "  \"allenatore\": \"COGNOME NOME\",\n"
        "  \"capitano_num\": 10,\n"
        "  \"vice_capitano_num\": 4,\n"
        "  \"data\": \"DD/MM/YYYY\",\n"
        "  \"campionato\": \"NOME CAMPIONATO\",\n"
        "  \"giocatori\": [\n"
        "    {\"numero\": 1, \"cognome_nome\": \"ROSSI ANDREA\", \"anno_nascita\": \"04\"}\n"
        "  ]\n"
        "}"
    )

    response = client.chat.completions.create(
        model=MODELLO,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Esegui l'estrazione OCR dei giocatori per: {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            },
        ],
        temperature=0.0,
    )

    risultato_grezzo = response.choices[0].message.content
    if not risultato_grezzo:
        raise ValueError(f"Il modello non ha restituito contenuto per la distinta {ruolo_squadra}.")

    try:
        dati = json.loads(risultato_grezzo.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Risposta AI non valida per la distinta {ruolo_squadra}: {e}") from e

    dati["allenatore"] = pulisci_testo(dati.get("allenatore"))
    dati["campionato"] = pulisci_testo(dati.get("campionato"))
    dati["data"] = pulisci_testo(dati.get("data"))

    giocatori_estratti = {}
    for g in dati.get("giocatori") or []:
        if not isinstance(g, dict):
            continue
        num = _to_int(g.get("numero"))
        if 1 <= num <= 20:
            giocatori_estratti[num] = {
                "cognome_nome": pulisci_testo(g.get("cognome_nome")),
                "anno_nascita": normalizza_anno(g.get("anno_nascita")),
            }

    cap_num = _to_int(dati.get("capitano_num"))
    vice_num = _to_int(dati.get("vice_capitano_num"))

    lista_20_giocatori = []
    for i in range(1, 21):
        if i in giocatori_estratti:
            nome_giocatore = giocatori_estratti[i]["cognome_nome"]
            if nome_giocatore:
                if i == cap_num and "(C)" not in nome_giocatore:
                    nome_giocatore += " (C)"
                elif i == vice_num and "(VC)" not in nome_giocatore:
                    nome_giocatore += " (VC)"
            lista_20_giocatori.append({
                "N°": i,
                "GIOCATORE": nome_giocatore,
                "ANNO": giocatori_estratti[i]["anno_nascita"],
            })
        else:
            lista_20_giocatori.append({"N°": i, "GIOCATORE": "", "ANNO": ""})

    dati["giocatori"] = lista_20_giocatori
    return dati
