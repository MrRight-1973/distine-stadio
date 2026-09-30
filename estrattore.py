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
    # Estrae solo i numeri consecutivi ignorando apici, punti o lettere (es. " '04 " -> "04")
    numeri = "".join(re.findall(r'\d+', str(anno_grezzo)))
    
    if len(numeri) == 2:
        # Se sono due cifre, gestisce il cambio di secolo (es. 98 -> 1998, 05 -> 2005)
        anno_int = int(numeri)
        return str(1900 + anno_int) if anno_int > 50 else str(2000 + anno_int)
    elif len(numeri) == 4:
        # Verifica che sia un anno plausibile (es. evita che prenda numeri di tessera a 4 cifre)
        anno_int = int(numeri)
        if 1970 <= anno_int <= 2015:
            return str(anno_int)
    return "" # Se il dato è palesemente incoerente, lascia vuoto per farlo correggere all'utente

def encode_image(uploaded_file):
    """Aumenta il contrasto interno e mantiene alta la risoluzione per l'OCR delle cifre"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((2000, 2000))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=95)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a GPT-4o con istruzioni matematiche stringenti sulla colonna ANNO"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        "Sei un sistema OCR ad altissima precisione per distinte LND.\n"
        "Concentrati sulla colonna dell'ANNO DI NASCITA (solitamente posizionata a destra del nome).\n\n"
        "REGOLE RIGIDE PER GLI ANNI:\n"
        "- Non confondere l'anno di nascita con il numero di maglia o con i codici di tesseramento.\n"
        "- Leggi l'anno esattamente come scritto (es. '04', '2005', '99'). Non inventarlo se la cella è vuota.\n"
        "- Inserisci il valore trovato nel campo 'anno_nascita' così come appare visivamente.\n\n"
        "Rispondi ESCLUSIVAMENTE con questo schema JSON:\n"
        "{\n"
        "  \"squadra\": \"NOME SOCIETA\",\n"
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
                    {"type": "text", "text": f"Esegui l'estrazione OCR focalizzandoti sulle date per la squadra {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    dati = json.loads(response.choices[0].message.content.strip())
    
    # Mappatura finale ordinata su 20 righe con validazione dell'anno
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                giocatori_estratti[num] = {
                    "cognome_nome": pulisci_testo(g.get("cognome_nome", "")),
                    "anno_nascita": normalizza_anno(g.get("anno_nascita", "")) # APPLICAZIONE FILTRO
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
