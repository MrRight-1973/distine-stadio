import json
import re
from openai import OpenAI
from utils import encode_image, pulisci_testo

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI ed estrae i dati in formato JSON identificando anche Capitano e Vice"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        f"Sei un assistente esperto di calcio LND. Il tuo compito attuale è scansionare la distinta della SQUADRA {ruolo_squadra}.\n"
        f"ATTENZIONE CRITICA: Devi estrarre esclusivamente il nome della società e dell'allenatore relativi alla squadra che gioca in {ruolo_squadra}. "
        "Non confonderla con la squadra avversaria.\n"
        "IDENTIFICAZIONE RUOLI: Cerca tra i giocatori chi è il Capitano (spesso indicato con (C), CAP, o una fascia) e il Vice Capitano (indicato con (VC), VICE, V.CAP).\n\n"
        "Rispondi ESCLUSIVAMENTE con un blocco json avente questa esatta struttura:\n"
        "{\n"
        "  \"squadra\": \"Nome Squadra\",\n"
        "  \"allenatore\": \"Cognome Nome\",\n"
        "  \"data\": \"DD/MM/YYYY\",\n"
        "  \"campionato\": \"Nome Campionato\",\n"
        "  \"numero_capitano\": 10,\n"
        "  \"numero_vice_capitano\": 4,\n"
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
                    {"type": "text", "text": f"Estrai l'elenco dei giocatori, Capitano/Vice, squadra e allenatore per la squadra {ruolo_squadra} in formato json."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices[0].message.content.strip()
    if risultato_grezzo.startswith("```"):
        risultato_grezzo = re.sub(r'^```(?:json)?\n', '', risultato_grezzo)
        risultato_grezzo = re.sub(r'\n```$', '', risultato_grezzo).strip()
        
    dati = json.loads(risultato_grezzo)
    
    dati["squadra"] = pulisci_testo(dati.get("squadra", "N.D."))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", "NON INDICATO"))
    dati["campionato"] = pulisci_testo(dati.get("campionato", "NON INDICATO"))
    dati["data"] = pulisci_testo(dati.get("data", "NON INDICATO"))
    
    num_cap = dati.get("numero_capitano")
    num_vice = dati.get("numero_vice_capitano")
    
    try:
        num_cap = int(num_cap) if num_cap is not None else None
    except:
        num_cap = None
        
    try:
        num_vice = int(num_vice) if num_vice is not None else None
    except:
        num_vice = None
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                nome_puro = pulisci_testo(g.get("cognome_nome", ""))
                
                # Aggiungiamo i suffissi ai nomi se corrispondono ai numeri rilevati
                if num == num_cap:
                    nome_puro += " (C)"
                elif num == num_vice:
                    nome_puro += " (VC)"
                    
                giocatori_estratti[num] = {
                    "cognome_nome": nome_puro,
                    "anno_nascita": str(g.get("anno_nascita", ""))
                }
        except:
            continue
            
    lista_20_giocatori = []
    for i in range(1, 21):
        if i in giocatori_estratti:
            lista_20_giocatori.append({
                "N°": i,
                "GIOCATORE": giocatori_estratti[i]["cognome_nome"],
                "ANNO": giocatori_estratti[i]["anno_nascita"]
            })
        else:
            lista_20_giocatori.append({"N°": i, "GIOCATORE": "", "ANNO": ""})
            
    dati["giocatori"] = lista_20_giocatori
    return dati
