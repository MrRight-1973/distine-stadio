import json
from openai import OpenAI
from utils import encode_image, pulisci_testo

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI sfruttando gli Structured Outputs (strict mode) per la massima precisione."""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    # Prompt di sistema potenziato per evitare scambi di squadra e isolare i ruoli
    prompt_sistema = (
        f"Sei un assistente esperto di calcio LND. Stai analizzando la distinta della squadra {ruolo_squadra}. "
        "Presta la massima attenzione: non confondere la squadra ospitante con la squadra ospite. "
        "Estrai i dati relativi unicamente alla distinta caricata.\n"
        "COMPITO AGGIUNTIVO SUI GIOCATORI:\n"
        "Identifica se vicino al nome di un giocatore è presente la lettera (C) o la parola 'Capitano', "
        "oppure (VC) / 'Vice'. Imposta il rispettivo campo booleano a true."
    )
    
    # Definizione del JSON Schema Strict per forzare l'accuratezza del modello
    json_schema_strict = {
        "name": "estrazione_distinta_gara",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "squadra": {"type": "string"},
                "allenatore": {"type": "string"},
                "data": {"type": "string"},
                "campionato": {"type": "string"},
                "giocatori": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "numero": {"type": "integer"},
                            "cognome_nome": {"type": "string"},
                            "anno_nascita": {"type": "string"},
                            "is_capitano": {"type": "boolean"},
                            "is_vice": {"type": "boolean"}
                        },
                        "required": ["numero", "cognome_nome", "anno_nascita", "is_capitano", "is_vice"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["squadra", "allenatore", "data", "campionato", "giocatori"],
            "additionalProperties": False
        }
    }
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        # Passiamo da semplice json_object a un json_schema con strict attivo
        response_format={
            "type": "json_schema",
            "json_schema": json_schema_strict
        },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Estrai con assoluta precisione la distinta per la squadra {ruolo_squadra}."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices[0].message.content.strip()
    dati = json.loads(risultato_grezzo)
    
    # Pulizia dati standard
    dati["squadra"] = pulisci_testo(dati.get("squadra", "N.D."))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", "NON INDICATO"))
    dati["campionato"] = pulisci_testo(dati.get("campionato", "NON INDICATO"))
    dati["data"] = pulisci_testo(dati.get("data", "NON INDICATO"))
    
    # Mappatura e formattazione con suffisso grafico temporaneo (es. ROSSI ANDREA (C))
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                nome_pulito = pulisci_testo(g.get("cognome_nome", ""))
                
                # Appendi visivamente il ruolo se intercettato dall'AI
                if g.get("is_capitano"):
                    nome_pulito += " (C)"
                elif g.get("is_vice"):
                    nome_pulito += " (VC)"
                    
                giocatori_estratti[num] = {
                    "cognome_nome": nome_pulito,
                    "anno_nascita": str(g.get("anno_nascita", ""))
                }
        except Exception:
            continue
            
    # Garantisce la struttura intatta da 1 a 20 righe per la griglia Streamlit
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
