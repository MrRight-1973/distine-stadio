import cv2
import re
import pytesseract

def genera_script_ispezione_visiva(percorso_immagine):
    print("=== AVVIO ANALISI GEOMETRICA E VISIVA ===")
    
    # 1. Carica l'immagine originale
    img_bgr = cv2.imread(percorso_immagine)
    if img_bgr is None:
        print(f"[Errore] Impossibile trovare o caricare l'immagine: {percorso_immagine}")
        return
        
    altezza_img, larghezza_img, _ = img_bgr.shape
    
    # 2. Pre-elaborazione in scala di grigi per l'OCR
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # 3. Estrazione coordinate da Tesseract
    dati_ocr = pytesseract.image_to_data(img_thresh, lang='ita', config='--psm 6', output_type=pytesseract.Output.DICT)
    
    col_nomi_left = None
    col_nomi_right = None
    col_nascita_left = None
    col_nascita_right = None
    
    n_elementi = len(dati_ocr['text'])
    
    # FASE 1: Rilevamento intestazioni
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

    # Fallback standard se le scritte dell'intestazione sono illeggibili
    if col_nomi_left is None:
        col_nomi_left, col_nomi_right = int(larghezza_img * 0.15), int(larghezza_img * 0.55)
    if col_nascita_left is None:
        col_nascita_left, col_nascita_right = int(larghezza_img * 0.58), int(larghezza_img * 0.85)

    # Disegna le colonne principali sull'immagine di output
    # Colonna Nomi = BLU, Colonna Nascita = VERDE
    cv2.rectangle(img_bgr, (col_nomi_left, 0), (col_nomi_right, altezza_img), (255, 0, 0), 3)
    cv2.rectangle(img_bgr, (col_nascita_left, 0), (col_nascita_right, altezza_img), (0, 255, 0), 3)

    # FASE 2: Raggruppamento per Y e disegno dei singoli tasselli rilevati
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
        
        # Evidenzia in ROSSO ogni parola trovata all'interno delle colonne target
        dentro_colonne = False
        if col_nomi_left <= x <= col_nomi_right or col_nascita_left <= x <= col_nascita_right:
            cv2.rectangle(img_bgr, (x, y), (x + w, y + h), (0, 0, 255), 1)
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

    # FASE 3: Stampa a terminale della lista finale pulita
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
            cognome = parole[0].upper()
            nome = " ".join(parole[1:]).title()
            riga_giocatore = f"{cognome} {nome}"
        else:
            riga_giocatore = parole[0].upper()
            
        if anno_pulito:
            riga_giocatore += f" ({anno_pulito})"
            
        giocatori_finali.append(riga_giocatore)

    giocatori_finali = list(dict.fromkeys(giocatori_finali))
    while len(giocatori_finali) < 20:
        giocatori_finali.append("--- Casella Vuota ---")
        
    print("\n[Output OCR] Giocatori rilevati su questo allineamento:")
    for idx, g in enumerate(giocatori_finali[:20], 1):
        print(f"{idx}. {g}")
        
    # Salva il file ispettivo sul disco per permetterti di guardarlo
    file_output = "risultato_colonne.jpg"
    cv2.imwrite(file_output, img_bgr)
    print(f"\n[Fatto] Mappa geometrica salvata con successo in: '{file_output}'")

# Esegui il test inserendo il nome della tua foto
# genera_script_ispezione_visiva("distinta.jpg")
