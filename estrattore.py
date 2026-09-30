import base64
import json
import io
import re
from PIL import Image
from openai import OpenAI

def pulisci_testo(testo):
    """Rimuove caratteri speciali inutili e standardizza in MAIUSCOLO"""
    if not testo or str(testo).strip() in ["", "N.D.", "NONE", "NULL"]:
        return ""
    testo_pulito = str(testo).replace("_", " ")
    testo_pulito = re.sub(r'\s+', ' ', testo_pulito)
    return testo_pulito.strip().upper()

def encode_image(uploaded_file):
    """Ridimensiona l'immagine per ottimizzare i costi e la precisione dell'OCR di OpenAI"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1800, 1800)) # Risoluzione leggermente maggiore per catturare meglio i testi piccoli
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=90)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI con prompt ultra-ottimizzato contro gli errori di lettura"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        "Sei un sistema OCR avanzato specializzato in distinte di gara della LND (Lega Nazionale Dilettanti).\n"
        "Il tuo obiettivo è estrarre i dati con precisione millimetrica. Evita assolutamente le allucinazioni.\n\n"
        "LINEE GUIDA RIGIDE:\n"
        "1. Analizza la griglia dei calciatori riga per riga, associando ogni giocatore al suo numero di maglia visibile a sinistra.\n"
        "2. Identifica il Capitano (cerca lettere 'C', 'CAP' o simboli/cerchi accanto al nome o al numero) e il Vice Capitano ('VC', 'VICE').\n"
        "3. Estrai l'anno di nascita (es. 2004, 2005, 98) in modo accurato. Se vedi solo due cifre (es. '03'), trasformalo in 4 cifre ('2003').\n"
        "4. Se un nome è parzialmente illeggibile, scrivi solo quello che leggi chiaramente. Non inventare.\n\n"
        "Rispondi ESCLUSIVAMENTE con un oggetto JSON avente questa struttura:\n"
        "{\n"
        "  \"squadra\": \"NOME DELLA SOCIETA\",\n"
        "  \"allenatore\": \"COGNOME NOME\",\n"
        "  \"capitano_num\": 10,\n"
        "  \"vice_capitano_num\": 4,\n"
        "  \"data\": \"DD/MM/YYYY\",\n"
        "  \"campionato\": \"NOME CAMPIONATO\",\n"
        "  \"giocatori\": [\n"
        "    {\"numero\": 1, \"cognome_nome\": \"ROSSI ANDREA\", \"anno_nascita\": \"2005\"}\n"
        "  ]\n"
        "}"
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Esegui l'estrazione OCR per la squadra {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0 # Forza la massima precisione deterministica
    )
    
    risultato_grezzo = response.choices[0].message.content.strip()
    dati = json.loads(risultato_grezzo)
    
    # Pulizia macro informazioni
    dati["squadra"] = pulisci_testo(dati.get("squadra", ""))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", ""))
    dati["campionato"] = pulisci_testo(dati.get("campionato", ""))
    dati["data"] = pulisci_testo(dati.get("data", ""))
    
    cap_num = int(dati.get("capitano_num", 0)) if str(dati.get("capitano_num", "")).isdigit() else 0
    vice_num = int(dati.get("vice_capitano_num", 0)) if str(dati.get("vice_capitano_num", "")).isdigit() else 0
    
    # Mappatura e normalizzazione a 20 righe fisse
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                giocatori_estratti[num] = {
                    "cognome_nome": pulisci_testo(g.get("cognome_nome", "")),
                    "anno_nascita": pulisci_testo(g.get("anno_nascita", ""))
                }
        except:
            continue
            
    lista_20_giocatori = []
    for i in range(1, 21):
        if i in giocatori_estratti:
            nome_giocatore = giocatori_estratti[i]["cognome_nome"]
            # Inietta le legende se non già presenti nel testo estratto
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
