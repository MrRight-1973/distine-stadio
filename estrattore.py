import base64
import json
import io
import re
from PIL import Image
from openai import OpenAI

def pulisci_testo(testo):
    """Rimuove caratteri speciali e standardizza rigorosamente in MAIUSCOLO"""
    if not testo or str(testo).strip() in ["", "N.D.", "NONE", "NULL", "NON INDICATO"]:
        return ""
    testo_pulito = str(testo).replace("_", " ")
    testo_pulito = re.sub(r'\s+', ' ', testo_pulito)
    return testo_pulito.strip().upper()

def encode_image(uploaded_file):
    """Mantiene un'alta risoluzione per non perdere i dettagli del testo piccolo"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((2000, 2000)) # Risoluzione aumentata a 2000px per massima leggibilità OCR
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=95)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a GPT-4o con un sistema di tracciamento riga per riga ad altissima precisione"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        "Sei un sistema OCR umano e scientifico specializzato nel digitalizzare distinte di gara di calcio LND.\n"
        "Devi scansionare il foglio con la massima attenzione ai dettagli visivi. Non inventare o allucinare.\n\n"
        "PROTOCOLLO DI ANALISI RIGIDO:\n"
        "1. Identifica il blocco della squadra richiesto. Trova il Nome della Società e l'Allenatore.\n"
        "2. Leggi la tabella principale dei calciatori procedendo esclusivamente RIGA PER RIGA da sinistra a destra.\n"
        "3. Per ogni riga, individua il numero di maglia (da 1 a 20). Se un numero non ha un giocatore scritto a fianco, ignoralo.\n"
        "4. Leggi il Cognome e Nome del giocatore: prenditi il tempo per decifrare tutte le lettere del cognome e del nome senza troncarle.\n"
        "5. Cerca con estrema cura i simboli del Capitano: se accanto al numero o al nome vedi una '(C)', 'C', 'CAP' o un cerchio, memorizza quel numero come capitano.\n"
        "6. Cerca i simboli del Vice Capitano: se vedi '(VC)', 'VC', 'V' o 'VICE', memorizza quel numero come vice capitano.\n"
        "7. Estrai l'Anno di Nascita in fondo alla riga. Se è scritto in formato a 2 cifre (es. '04'), convertilo sempre in 4 cifre ('2004'). Se vedi '99', convertilo in '1999'.\n\n"
        "Rispondi ESCLUSIVAMENTE con un file JSON valido strutturato così:\n"
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
        model="gpt-4o", # PASSAGGIO CHIAVE: Usiamo gpt-4o standard (visione nettamente superiore rispetto a gpt-4o-mini)
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Esegui la scansione e l'estrazione dati della squadra: {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices[0].message.content.strip()
    dati = json.loads(risultato_grezzo)
    
    # Pulizia e standardizzazione macro dati
    dati["squadra"] = pulisci_testo(dati.get("squadra", ""))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", ""))
    dati["campionato"] = pulisci_testo(dati.get("campionato", ""))
    dati["data"] = pulisci_testo(dati.get("data", ""))
    
    cap_num = int(dati.get("capitano_num", 0)) if str(dati.get("capitano_num", "")).isdigit() else 0
    vice_num = int(dati.get("vice_capitano_num", 0)) if str(dati.get("vice_capitano_num", "")).isdigit() else 0
    
    # Mappatura finale ordinata su 20 righe
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
            # Gestione pulita dei tag Capitano e Vice
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
