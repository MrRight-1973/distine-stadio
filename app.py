import time  # Assicurati che questo import sia presente in cima al file se non c'è

def analizza_distinta_con_ia(immagine_pil, client):
    prompt = (
        "Analizza questa immagine di una distinta di gara di calcio. "
        "Estrai accuratamente il nome della squadra, il nome dell'allenatore, "
        "l'allenatore in seconda (se presente) e la lista di tutti i giocatori "
        "con il loro anno di nascita (calcolato o letto dalla data di nascita) "
        "e l'eventuale ruolo di capitano/vice."
    )
    
    # Usiamo solo il modello ufficiale di nuova generazione
    modello_attivo = 'gemini-3.8-flash'
    massimi_tentativi = 3
    
    for tentativo in range(massimi_tentativi):
        try:
            response = client.models.generate_content(
                model=modello_attivo,
                contents=[immagine_pil, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SquadraDati,
                    temperature=0.1
                ),
            )
            return json.loads(response.text)
            
        except APIError as e:
            # Se il server è occupato (503) o c'è un picco di richieste, aspetta e riprova
            if e.code in [503, 429] and tentativo < massimi_tentativi - 1:
                time.sleep(2)  # Aspetta 2 secondi prima del prossimo tentativo
                continue
            else:
                raise e
        except Exception as e:
            raise e
            
    raise Exception("I server di Google sono temporaneamente sovraccarichi. Riprova tra pochi secondi.")
