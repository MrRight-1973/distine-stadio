import json
import re
from openai import OpenAI
from utils import encode_image, pulisci_testo

def estrai_solo_anno(testo_anno):
    """
    Cerca una sequenza di 4 cifre consecutive (es. 2005) nel testo.
    Se l'AI ha inserito una data intera (es. 12/04/2005 o 05-06-2002),
    estrae e restituisce solo l'anno a 4 cifre.
    """
    if not testo_anno:
        return ""
    testo_stringa = str(testo_anno).strip()
    match = re.search(r'\b(19\d{2}|20\d{2})\b', testo_stringa)
    if match:
        return match.group(1)
    return ""

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI sfruttando gli Structured Outputs (strict mode) con post-processing di precisione."""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        f"Sei un assistente esperto di calcio LND. Stai analizzando la distinta della squadra {ruolo_squadra}.\n"
        "REGOLE TASSATIVE DI PRECISIONE:\n"
        "1. ANNO DI NASCITA: Estrai UNICAMENTE l'anno di nascita a 4 cifre (es. '2004'). Non inserire MAI la data completa (GG/MM/AAAA).\n"
        "2. CAPITANO E VICE: Identifica se vicino al nome è presente (C)/'Capitano' o (VC)/'Vice'. "
        "Può esserci AL MASSIMO un solo capitano (is_capitano: true) e un solo vice capitano (is_vice: true) per tutta la squadra. "
        "Non duplicare mai questi ruoli."
    )
    
    json_schema_strict = {
        "name": "estrazione_distinta_gara_regolata",
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
        response_format={
            "type": "json_schema",
            "json_schema": json_schema_strict
        },
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Estrai i dati della squadra {ruolo_squadra} rispettando i vincoli di anno e ruoli."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.0
    )
    
    risultato_grezzo = response.choices[0].message.content.strip()
    dati = json.loads(risultato_grezzo)
    
    # Pulizia metadati generali
    dati["squadra"] = pulisci_testo(dati.get("squadra", "N.D."))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", "NON INDICATO"))
    dati["campionato"] = pulisci_testo(dati.get("campionato", "NON INDICATO"))
    dati["data"] = pulisci_testo(dati.get("data", "NON INDICATO"))
    
    # Variabili di controllo per evitare duplicati di Capitano e Vice via codice
    capitano_assegnato = False
    vice_assegnato = False
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                nome_pulito = pulisci_testo(g.get("cognome_nome", ""))
                
                # Correzione forzata dell'anno (estirpa le date intere nel caso l'AI fallisse il prompt)
                anno_pulito = estrai_solo_anno(g.get("anno_nascita", ""))
                
                # Gestione rigorosa dei ruoli: assegna il tag solo se non è già stato assegnato prima
                if g.get("is_capitano") and not capitano_assegnato:
                    nome_pulito += " (C)"
                    capitano_assegnato = True
                elif g.get("is_vice") and not vice_assegnato:
                    nome_pulito += " (VC)"
                    vice_assegnato = True
                    
                giocatori_estratti[num] = {
                    "cognome_nome": nome_pulito,
                    "anno_nascita": anno_pulito
                }
        except Exception:
            continue
            
    # Rigenerazione della lista fissa a 20 righe per Streamlit
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
