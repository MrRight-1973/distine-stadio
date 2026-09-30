import json
import re
from openai import OpenAI
from utils import encode_image, pulisci_testo

def estrai_solo_anno(testo_anno):
    """Estrae solo la sequenza di 4 cifre consecutive dell'anno (es. 2005)."""
    if not testo_anno:
        return ""
    testo_stringa = str(testo_anno).strip()
    match = re.search(r'\b(19\d{2}|20\d{2})\b', testo_stringa)
    if match:
        return match.group(1)
    return ""

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI in Strict Mode con controlli di tolleranza avanzati per Capitani/Vice."""
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
        response_format={"type": "json_schema", "json_schema": json_schema_strict},
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
    
    risultato_grezzo = response.choices.message.content.strip()
    dati = json.loads(risultato_grezzo)
    
    dati["squadra"] = pulisci_testo(dati.get("squadra", "N.D."))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", "NON INDICATO"))
    dati["campionato"] = pulisci_testo(dati.get("campionato", "NON INDICATO"))
    dati["data"] = pulisci_testo(dati.get("data", "NON INDICATO"))
    
    capitano_assegnato = False
    vice_assegnato = False
    
    giocatori_estratti = {}
    for g in dati.get("giocatori", []):
        try:
            num = int(g.get("numero", 0))
            if 1 <= num <= 20:
                nome_originale = str(g.get("cognome_nome", "")).upper()
                
                # --- ALGORITMO DI FALLBACK TESTUALE ---
                # Se l'AI ha mancato il flag booleano ma ha scritto il tag nel nome, lo intercettiamo
                is_cap_testo = bool(re.search(r'\b(C|CAP|CAPITANO)\b', nome_originale)) or g.get("is_capitano")
                is_vice_testo = bool(re.search(r'\b(VC|VICE|VICE-CAPITANO)\b', nome_originale)) or g.get("is_vice")
                
                # Puliamo i vecchi tag dal nome per evitare stringhe disordinate come "ROSSI (C) (C)"
                nome_pulito = re.sub(r'[\(\[\{]?(C|VC|CAP|CAPITANO|VICE)[\)\]\}]?', '', nome_originale)
                nome_pulito = pulisci_testo(nome_pulito)
                
                # Assegnazione rigorosa senza duplicati
                if is_cap_testo and not capitano_assegnato:
                    nome_pulito += " (C)"
                    capitano_assegnato = True
                elif is_vice_testo and not vice_assegnato:
                    nome_pulito += " (VC)"
                    vice_assegnato = True
                    
                giocatori_estratti[num] = {
                    "cognome_nome": nome_pulito,
                    "anno_nascita": estrai_solo_anno(g.get("anno_nascita", ""))
                }
        except Exception:
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
