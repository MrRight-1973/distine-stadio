import re
import io
from PIL import Image, ImageEnhance, ImageDraw
import pytesseract

def genera_script_ispezione_visiva_pil(uploaded_file):
    print("=== AVVIO ANALISI GEOMETRICA CON MOTORE PIL ===")
    
    try:
        # 1. Carica l'immagine originale e crea una copia a colori per il disegno
        img_originale = Image.open(uploaded_file)
        img_disegno = img_originale.convert("RGB")
        draw = ImageDraw.Draw(img_disegno)
        
        larghezza_img, altezza_img = img_originale.size
        
        # 2. Pre-elaborazione in scala di grigi ad alto contrasto per l'OCR
        img_ocr = img_originale.convert('L')
        img_ocr = ImageEnhance.Contrast(img_ocr).enhance(3.0)
        
        # 3. Estrazione coordinate spaziali da Tesseract
        dati_ocr = pytesseract.image_to_data(img_ocr, lang='ita', config='--psm 6', output_type=pytesseract.Output.DICT)
        
        col_nomi_left = None
        col_nomi_right = None
        col_nascita_left = None
        col_nascita_right = None
        
        n_elementi = len(dati_ocr['text'])
        
        # FASE 1: Individuazione automatica delle colonne tramite intestazioni
        for i in range(n_elementi):
            testo = str(dati_ocr['text'][i]).upper().strip()
            
            if "COGNOME" in testo or "NOME" in testo:
                if col_nomi_left is None:
                    col_nomi_left = dati_ocr['left'][i] - 20
                    col_nomi_right = col_nomi_left + 450
                    
            if "NASCITA" in testo or "DATA" in testo or "NASC" in testo:
                if col_nascita_left is None:
                    col_nascita_left = dati_ocr['left'][i] - 15
                    col_nascita_right = col_nascita_left + 180

        # Fallback se le scritte dell'intestazione sono illeggibili o sbiadite
        if col_nomi_left is None:
            col_nomi_left, col_nomi_right = int(larghezza_img * 0.15), int(larghezza_img * 0.55)
        if col_nascita_left is None:
            col_nascita_left, col_nascita_right = int(larghezza_img * 0.58), int(larghezza_img * 0.85)

        # Disegna le colonne principali (Nomi = BLU, Nascita = VERDE) con spessore 4px
        draw.rectangle([col_nomi_left, 0, col_nomi_right, altezza_img], outline="blue", width=4)
        draw.rectangle([col_nascita_left, 0, col_nascita_right, altezza_img], outline="green", width=4)

        # FASE 2: Raggruppamento per Y e disegno dei tasselli letti
        righe_mappate = {}
        tolleranza_y = 12 
        
        for i in range(n_elementi):
            testo_parola = str(dati_ocr['text'][i]).strip()
            confidenza = int(dati_ocr['conf'][i])
            
            if confidenza < 35 or len(testo_parola) < 2:
                continue
                
            x = dati_ocr['left'][i]
            y = dati_ocr['top'][i]
            w = dati_ocr['width'][i]
            h = dati_ocr['height'][i]
            
            dentro_colonne = False
            if col_nomi_left <= x <= col_nomi_right or col_nascita_left <= x <= col_nascita_right:
                # Evidenzia in ROSSO ogni singola parola intercettata
                draw.rectangle([x, y, x + w, y + h], outline="red", width=1)
                dentro_colonne = True
                
            if dentro_colonne:
                riga_y = None
                for y_chiave in righe_mappate.keys():
                    if abs(y_chiave - y) <= tolleranza_y:
                        riga_y = y_chiave
                        break
                
                if riga_y is None:
                    riga_y = y
                    righe_mappate[riga_y] = {"nomi": [], "nascita": []}
                    
                if col_nomi_left <= x <= col_nomi_right:
                    if not any(z in testo_parola.upper() for z in ["COGNOME", "NOME", "ALLENATORE"]):
                        righe_mappate[riga_y]["nomi"].append(testo_parola)
                elif col_nascita_left <= x <= col_nascita_right:
                    if not any(z in testo_parola.upper() for z in ["NASCITA", "DATA", "ANNO"]):
                        righe_mappate[riga_y]["nascita"].append(testo_parola)

        # FASE 3: Generazione della lista dei 20 giocatori per il terminale
        giocatori_finali = []
        for y in sorted(righe_mappate.keys()):
            stringa_nome = " ".join(righe_mappate[y]["nomi"]).strip()
            stringa_nascita = "".join(righe_mappate[y]["nascita"]).strip()
            
            if not stringa_nome or len(re.sub(r'[^a-zA-Z]', '', stringa_nome)) < 3:
                continue
                
            match_anno = re.search(r'\b(\d{2,4})\b', stringa_nascita)
            anno_pulito = f"'{match_anno.group(1)[-2:]}" if match_anno else ""
            
            parole = stringa_nome.split()
            if len(parole) >= 2:
                cognome = parole.upper()
                nome = " ".join(parole[1:]).title()
                riga_giocatore = f"{cognome} {nome}"
            else:
                riga_giocatore = parole.upper()
                
            if anno_pulito:
                riga_giocatore += f" ({anno_pulito})"
                
            giocatori_finali.append(riga_giocatore)

        giocatori_finali = list(dict.fromkeys(giocatori_finali))
        while len(giocatori_finali) < 20:
            giocatori_finali.append("--- Casella Vuota ---")
            
        print("\n[Output OCR] Giocatori rilevati:")
        for idx, g in enumerate(giocatori_finali[:20], 1):
            print(f"{idx}. {g}")
            
        # Salva l'immagine con i rettangoli disegnati per il controllo visivo
        img_disegno.save("risultato_colonne.jpg")
        print("\n[Fatto] Immagine ispettiva salvata in 'risultato_colonne.jpg'")
        
    except Exception as e:
        print(f"\n[Errore] Impossibile completare l'estrazione: {str(e)}")
