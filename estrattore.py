import base64
import json
import io
import re
from PIL import Image
from openai import OpenAI

def pulisci_testo(testo):
    """Rimuove caratteri speciali inutili e standardizza in MAIUSCOLO"""
    if not testo or str(testo).strip() in ["", "N.D.", "NONE", "NULL", "NON INDICATO"]:
        return ""
    testo_pulito = str(testo).replace("_", " ")
    testo_pulito = re.sub(r'\s+', ' ', testo_pulito)
    return testo_pulito.strip().upper()

def normalizza_anno(anno_grezzo):
    """Isola l'anno numerico e lo forza rigorosamente nel formato a 4 cifre (YYYY)"""
    if not anno_grezzo:
        return ""
    numeri = "".join(re.findall(r'\d+', str(anno_grezzo)))
    if len(numeri) == 2:
        anno_int = int(numeri)
        return str(1900 + anno_int) if anno_int > 50 else str(2000 + anno_int)
    elif len(numeri) == 4:
        anno_int = int(numeri)
        if 1970 <= anno_int <= 2015:
            return str(anno_int)
    return ""

def encode_image(uploaded_file):
    """Mantiene alta la risoluzione per l'OCR delle cifre"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((2000, 2000))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=95)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Estrae SOLO l'allenatore, i giocatori e le date per la specifica squadra"""
    client = OpenAI(api_key=api_key)
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
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Esegui l'estrazione OCR dei giocatori per: {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices.message.content.strip()
    if risultato_grezzo.startswith("```"):
        risultato_grezzo = re.sub(r'^```(?:json)?\n', '', risultato_grezzo)
        risultato_grezzo = re.sub(r'\n```$', '', risultato_grezzo).strip()
        
    dati = json.loads(risultato_grezzo)
    
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", ""))
    dati["campionato"] = pulisci_testo(dati.get("campionato", ""))
    dati["data"] = pulisci_testo(dati.get("data", ""))
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                giocatori_estratti[num] = {
                    "cognome_nome": pulisci_testo(g.get("cognome_nome", "")),
                    "anno_nascita": normalizza_anno(g.get("anno_nascita", ""))
                }
        except:
            continue
            
    lista_20_giocatori = []
    cap_num = int(dati.get("capitano_num", 0)) if str(dati.get("capitano_num", "")).isdigit() else 0
    vice_num = int(dati.get("vice_capitano_num", 0)) if str(dati.get("vice_capitano_num", "")).isdigit() else 0

    for i in range(1, 21):
        if i in giocatori_estratti:
            nome_giocatore = giocatori_estratti[i]["cognome_nome"]
            if i == cap_num and "(C)" not in nome_giocatore:
                nome_giocatore += " (C)"
            elif i == vice_num and "(VC)" not in nome_giocatore:
                nome_giocatore += " (VC)"
                
            lista_20_giocatori.append({
                "N°": i,
                "GIOCATORE": nome_giocatore,
                "ANNO": giocatori_estratti[i]["anno_nascita"]
            })
        else:
            lista_20_giocatori.append({"N°": i, "GIOCATORE": "", "ANNO": ""})
            
    dati["giocatori"] = lista_20_giocatori
    return dati
