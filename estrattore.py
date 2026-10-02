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


MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
    "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
    "gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6,
    "lug": 7, "ago": 8, "set": 9, "sett": 9, "ott": 10, "nov": 11, "dic": 12,
}


def normalizza_data(data_grezza):
    """Riporta la data della gara nel formato GG/MM/AAAA, oppure "" se non è credibile.

    Accetta 02/11/2025, 2-11-25, 02.11.2025, "2 novembre 2025". Anni a 2 cifre = 20xx.
    Una data di gara realistica è tra tre anni fa e l'anno prossimo: questo
    scarta, per esempio, una data di nascita letta per errore.
    """
    if not data_grezza:
        return ""
    testo = str(data_grezza).strip().lower()

    giorno = mese = anno = None
    m = re.search(r"(\d{1,2})\s*[/\-.\s]\s*(\d{1,2})\s*[/\-.\s]\s*(\d{4}|\d{2})\b", testo)
    if m:
        giorno, mese, anno = int(m[1]), int(m[2]), int(m[3])
    else:
        m = re.search(r"(\d{1,2})\s*(?:°|º)?\s*([a-zà]+)\.?\s*(\d{4}|\d{2})\b", testo)
        if m and m[2] in MESI:
            giorno, mese, anno = int(m[1]), MESI[m[2]], int(m[3])
    if anno is None:
        return ""
    if anno < 100:
        anno += 2000

    anno_corrente = datetime.now().year
    if not (anno_corrente - 3 <= anno <= anno_corrente + 1):
        return ""
    try:
        return datetime(anno, mese, giorno).strftime("%d/%m/%Y")
    except ValueError:
        return ""


def unisci_scansioni(casa_raw, ospite_raw):
    """Riunisce i dati letti dalle due distinte, completando ciò che manca in una con l'altra.

    Ogni foto può riportare solo la propria squadra oppure l'intestazione della gara
    con entrambe: si usa la lettura più diretta e, se manca, quella dell'altra foto.
    """
    def primo(*valori):
        return next((v for v in valori if v), "")

    return {
        "campionato": primo(casa_raw.get("campionato"), ospite_raw.get("campionato")),
        "data": primo(casa_raw.get("data"), ospite_raw.get("data")),
        "nome_casa": primo(casa_raw.get("squadra"), casa_raw.get("squadra_casa"), ospite_raw.get("squadra_casa")),
        "nome_ospite": primo(ospite_raw.get("squadra"), ospite_raw.get("squadra_ospite"), casa_raw.get("squadra_ospite")),
        "all_casa": casa_raw.get("allenatore", ""),
        "all_ospite": ospite_raw.get("allenatore", ""),
    }


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
    """Estrae società, data, campionato, allenatore e giocatori per la specifica squadra"""
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
        "1. Trova il NOME DELLA SOCIETA' della sezione indicata (di solito nell'intestazione, vicino a "
        "'Società' o 'Squadra'), scritto per esteso. Se non è leggibile con certezza usa \"\": non inventarlo.\n"
        "2. Se la distinta riporta anche l'intestazione della gara (per esempio 'Gara: SQUADRA A - SQUADRA B'), "
        "riporta in squadra_casa la prima e in squadra_ospite la seconda; altrimenti usa \"\" per entrambe.\n"
        "3. Trova la DATA DELLA GARA (vicino a 'Data' o 'Data gara') in formato GG/MM/AAAA con anno a 4 cifre. "
        "NON confonderla con gli anni di nascita dei calciatori né con altre date (rilascio tessere, firme). "
        "Se non c'è, usa \"\".\n"
        "4. Trova l'Allenatore della sezione indicata.\n"
        "5. Concentrati sulla colonna dei CALCIATORI e dell'ANNO DI NASCITA riga per riga.\n"
        "6. Cerca la sigla del Capitano (C, CAP) e del Vice (VC, VICE) accanto al nome o al numero.\n\n"
        "Rispondi ESCLUSIVAMENTE con questo schema JSON:\n"
        "{\n"
        "  \"squadra\": \"NOME SOCIETA' DELLA SEZIONE ANALIZZATA\",\n"
        "  \"squadra_casa\": \"\",\n"
        "  \"squadra_ospite\": \"\",\n"
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
    dati["data"] = normalizza_data(dati.get("data"))
    dati["squadra"] = pulisci_testo(dati.get("squadra"))
    dati["squadra_casa"] = pulisci_testo(dati.get("squadra_casa"))
    dati["squadra_ospite"] = pulisci_testo(dati.get("squadra_ospite"))

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
