import json
import re
from openai import OpenAI
from utils import encode_image, pulisci_testo

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI ed estrae i dati in formato JSON identificando Capitano, Vice e Giocatori"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    # PROMPT AVANZATO PER ERRORI ORTOGRAFICI E DATE DI NASCITA
    prompt_sistema = (
        f"Sei un assistente esperto di calcio LND. Il tuo compito attuale è scansionare con la massima precisione "
        f"visiva la distinta della SQUADRA {ruolo_squadra}.\n\n"
        f"ATTENZIONE DETTAGLI ORTOGRAFICI:\n"
        f"- Isola e leggi con cura ogni lettera dei COGNOMI e NOMI. Evita di confondere lettere simili (es. 'O' con 'D', 'I' con 'L', 'G' con 'C').\n"
        f"- Se un nome ti sembra strano o troncato, correggilo basandoti sulla logica dei nomi e cognomi italiani comuni.\n\n"
        f"ATTENZIONE DATE DI NASCITA / ANNO:\n"
        f"- Trova l'anno di nascita di ogni calciatore (solitamente indicato nell'ultima colonna della griglia).\n"
        f"- Restituisci l'anno SEMPRE nel formato a 4 cifre (es. se leggi '05' convertilo in '2005', se leggi '98' in '1998').\n"
        f"- Se l'anno è parzialmente illeggibile o confuso, fai del tuo meglio per dedurre le 4 cifre logiche (es. un giovane calciatore LND sarà tipicamente nato tra il 1995 e il 2009).\n\n"
        f"RICERCA RUOLI REGOLAMENTARI:\n"
        f"- Identifica il numero del Capitano (indicato da (C), CAP, asterischi, o cerchi sul numero).\n"
        f"- Identifica il numero del Vice Capitano (indicato da (VC), VICE, V.CAP).\n\n"
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
    
    # Passiamo al modello gpt-4o ad altissima risoluzione visiva per azzerare i refusi
    response = client.chat.completions.create(
        model="gpt-4o", 
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Estrai con la massima precisione visiva i dati della squadra {ruolo_squadra}. Correggi gli anni a 4 cifre e controlla i refusi nei nomi."},
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
    
    try: num_cap = int(num_cap) if num_cap is not None else None
    except: num_cap = None
        
    try: num_vice = int(num_vice) if num_vice is not None else None
    except: num_vice = None
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                nome_puro = pulisci_testo(g.get("cognome_nome", ""))
                
                # Pulizia stringhe residue di ruoli lette dall'AI nel testo
                nome_puro = nome_puro.replace("(C)", "").replace("(VC)", "").strip()
                
                if num == num_cap:
                    nome_puro += " (C)"
                elif num == num_vice:
                    nome_puro += " (VC)"
                
                # SCRIPT DI CONTROLLO ANNO: Forza la formattazione corretta a 4 cifre a livello codice
                anno_grezzo = str(g.get("anno_nascita", "")).strip()
                anno_pulito = re.sub(r'\D', '', anno_grezzo) # Rimuove eventuali caratteri non numerici
                
                if len(anno_pulito) == 2:
                    # Se legge due cifre (es. '03'), deduce il secolo corretto
                    anno_int = int(anno_pulito)
                    anno_grezzo = f"20{anno_pulito}" if anno_int <= 30 else f"19{anno_pulito}"
                elif len(anno_pulito) == 4:
                    anno_grezzo = anno_pulito
                else:
                    # Lascia il valore originale o vuoto se non interpretabile
                    anno_grezzo = anno_pulito if anno_pulito else ""

                giocatori_estratti[num] = {
                    "cognome_nome": nome_puro,
                    "anno_nascita": anno_grezzo
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
