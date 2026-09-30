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
    """Aumenta il contrasto interno e mantiene alta la risoluzione per l'OCR delle cifre"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((2000, 2000))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=95)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a GPT-4o focalizzando l'attenzione sul ruolo specifico (CASA o OSPITE)"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    # Istruzione dinamica e severa basata sul ruolo della squadra per evitare scambi di dati
    focus_ruolo = (
        "ATTENZIONE: Stai analizzando la SQUADRA IN OSPITE (colonna/sezione OSPITI o FUORI CASA). "
        "Ignora completamente i giocatori della squadra di casa se presenti nella stessa immagine."
        if ruolo_squadra == "OSPITE" else
        "ATTENZIONE: Stai analizzando la SQUADRA IN CASA (colonna/sezione LOCALI o IN CASA). "
        "Ignora completamente i giocatori della squadra ospite se presenti nella stessa immagine."
    )
    
    prompt_sistema = (
        f"Sei un sistema OCR umano ad altissima precisione per distinte LND.\n"
        f"{focus_ruolo}\n\n"
        "REGOLE RIGIDE DI SCANSIONE:\n"
        "1. Trova il Nome della Società Corretta e il relativo Allenatore della sezione indicata.\n"
        "2. Concentrati sulla colonna dell'ANNO DI NASCITA di questa specifica squadra. "
        "Assicurati di non scambiare le righe: il giocatore N°5 deve avere l'anno scritto sulla sua stessa riga.\n"
        "3. Non confondere l'anno di nascita con codici tessera o numeri di maglia.\n"
        "4. Cerca la sigla del Capitano (C, CAP) e del Vice (VC, VICE) solo per questa squadra.\n\n"
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
                    {"type": "text", "text": f"Esegui l'estrazione OCR per la squadra: {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    dati = json.loads(response.choices.message.content.strip())
    
    # Pulizia macro informazioni
    dati["squadra"] = pulisci_testo(dati.get("squadra", ""))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", ""))
    dati["campionato"] = pulisci_testo(dati.get("campionato", ""))
    dati["data"] = pulisci_testo(dati.get("data", ""))
    
    # Mappatura ordinata su 20 righe fisse
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
