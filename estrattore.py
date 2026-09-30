import base64
import json
import io
import re
from PIL import Image
from openai import OpenAI

def pulisci_testo(testo):
    """Rimuove i caratteri speciali come _ e converte tutto in MAIUSCOLO"""
    if not testo or str(testo).strip() == "":
        return ""
    testo_pulito = str(testo).replace("_", " ")
    testo_pulito = re.sub(r'\s+', ' ', testo_pulito)
    return testo_pulito.strip().upper()

def encode_image(uploaded_file):
    """Apre l'immagine, la ridimensiona se troppo grande e la converte in stringa Base64"""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1600, 1600))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=85)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')

def analizza_distinta(uploaded_file, ruolo_squadra, api_key):
    """Invia la foto a OpenAI ed estrae i dati in formato JSON inclusi capitano, vice e guardalinee"""
    client = OpenAI(api_key=api_key)
    base64_image = encode_image(uploaded_file)
    
    prompt_sistema = (
        "Sei un assistente esperto di calcio LND. Il tuo compito è scansionare la distinta di gara.\n"
        "Identifica i calciatori, il capitano (spesso indicato con C, CAP o cerchiato), il vice capitano (VC o VICE) "
        "e il guardalinee di parte (assistente di parte / dirigente guardalinee indicato sulla distinta).\n"
        "Rispondi ESCLUSIVAMENTE con un blocco json avente questa esatta struttura:\n"
        "{\n"
        "  \"squadra\": \"Nome Squadra\",\n"
        "  \"allenatore\": \"Cognome Nome\",\n"
        "  \"capitano_num\": 10,\n"
        "  \"vice_capitano_num\": 4,\n"
        "  \"guardalinee_parte\": \"Cognome Nome\",\n"
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
                    {"type": "text", "text": f"Estrai i dati e l'elenco dei giocatori per la squadra {ruolo_squadra} in formato json."},
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
    
    # Pulizia macro informazioni
    dati["squadra"] = pulisci_testo(dati.get("squadra", "N.D."))
    dati["allenatore"] = pulisci_testo(dati.get("allenatore", "NON INDICATO"))
    dati["campionato"] = pulisci_testo(dati.get("campionato", "NON INDICATO"))
    dati["data"] = pulisci_testo(dati.get("data", "NON INDICATO"))
    dati["guardalinee_parte"] = pulisci_testo(dati.get("guardalinee_parte", ""))
    
    try:
        dati["capitano_num"] = int(dati.get("capitano_num", 0))
    except:
        dati["capitano_num"] = 0
        
    try:
        dati["vice_capitano_num"] = int(dati.get("vice_capitano_num", 0))
    except:
        dati["vice_capitano_num"] = 0
    
    # Mappatura e normalizzazione a 20 righe standard
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
        ruolo_nota = ""
        if i == dati["capitano_num"]:
            ruolo_nota = " (C)"
        elif i == dati["vice_capitano_num"]:
            ruolo_nota = " (VC)"
            
        if i in giocatori_estratti:
            lista_20_giocatori.append({
                "N°": i,
                "GIOCATORE": giocatori_estratti[i]["cognome_nome"] + ruolo_nota,
                "ANNO": giocatori_estratti[i]["anno_nascita"]
            })
        else:
            lista_20_giocatori.append({"N°": i, "GIOCATORE": "", "ANNO": ""})
            
    dati["giocatori"] = lista_20_giocatori
    return dati
