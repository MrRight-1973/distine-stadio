import json
import re
from openai import OpenAI
from utils import encode_image, pulisci_testo

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI ed estrae i dati in formato JSON garantendo 20 righe strutturate"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    # PROMPT OTTIMIZZATO: Specifichiamo all'AI di concentrarsi SOLO sul ruolo richiesto (CASA o OSPITE)
    prompt_sistema = (
        f"Sei un assistente esperto di calcio LND. Il tuo compito attuale è scansionare la distinta della SQUADRA {ruolo_squadra}.\n"
        f"ATTENZIONE CRITICA: Devi estrarre esclusivamente il nome della società e dell'allenatore relativi alla squadra che gioca in {ruolo_squadra}. "
        "Non confonderla con la squadra avversaria eventualmente menzionata nell'intestazione del foglio.\n\n"
        "Rispondi ESCLUSIVAMENTE con un blocco json avente questa esatta struttura:\n"
        "{\n"
        "  \"squadra\": \"Nome Squadra " + ruolo_squadra + "\",\n"
        "  \"allenatore\": \"Cognome Nome Allenatore\",\n"
        "  \"data\": \"DD/MM/YYYY\",\n"
        "  \"campionato\": \"Nome Campionato\",\n"
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
                    {"type": "text", "text": f"Estrai l'elenco dei giocatori, il nome esatto della squadra e l'allenatore per la squadra con ruolo {ruolo_squadra} in formato json."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0  # Mantenuto a 0.0 per la massima precisione e determinismo
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
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                giocatori_estratti[num] = {
                    "cognome_nome": pulisci_testo(g.get("cognome_nome", "")),
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
