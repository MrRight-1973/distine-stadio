# Sostituisci il blocco finale del codice (dove c'è il pulsante di estrazione) con questo:

if foto_casa and foto_ospite:
    st.markdown("### 🔍 1. Analisi e verifica geometrica delle colonne")
    
    if st.button("🚀 AVVIA ESTRAZIONE PURA DALLE FOTO", use_container_width=True):
        with st.spinner("Il motore spaziale sta tracciando le coordinate X/Y delle colonne..."):
            
            # Eseguiamo la funzione PIL pura sulla foto CASA passandogli direttamente il file caricato
            # (Adattiamo la funzione precedente per ritornare sia i dati che l'immagine disegnata)
            def analizza_e_disegna_squadra(uploaded_file, etichetta_squadra):
                img_originale = Image.open(uploaded_file)
                img_disegno = img_originale.convert("RGB")
                draw = ImageDraw.Draw(img_disegno)
                
                larghezza_img, altezza_img = img_originale.size
                img_ocr = img_originale.convert('L')
                img_ocr = ImageEnhance.Contrast(img_ocr).enhance(3.0)
                
                dati_ocr = pytesseract.image_to_data(img_ocr, lang='ita', config='--psm 6', output_type=pytesseract.Output.DICT)
                
                col_nomi_left = None
                col_nomi_right = None
                col_nascita_left = None
                col_nascita_right = None
                n_elementi = len(dati_ocr['text'])
                
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

                if col_nomi_left is None:
                    col_nomi_left, col_nomi_right = int(larghezza_img * 0.15), int(larghezza_img * 0.55)
                if col_nascita_left is None:
                    col_nascita_left, col_nascita_right = int(larghezza_img * 0.58), int(larghezza_img * 0.85)

                # Disegniamo i rettangoli di controllo visivo
                draw.rectangle([col_nomi_left, 0, col_nomi_right, altezza_img], outline="blue", width=6)
                draw.rectangle([col_nascita_left, 0, col_nascita_right, altezza_img], outline="green", width=6)

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
                    
                    if col_nomi_left <= x <= col_nomi_right or col_nascita_left <= x <= col_nascita_right:
                        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                        
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
                        riga_giocatore = parole[0].upper() if parole else ""
                        
                    if anno_pulito and riga_giocatore:
                        riga_giocatore += f" ({anno_pulito})"
                    if riga_giocatore:
                        giocatori_finali.append(riga_giocatore)

                giocatori_finali = list(dict.fromkeys(giocatori_finali))
                while len(giocatori_finali) < 20:
                    giocatori_finali.append("")
                return giocatori_finali[:20], img_disegno

            # Esecuzione per le due foto caricate dall'utente nei componenti st.file_uploader
            g_casa, img_visto_casa = analizza_e_disegna_squadra(foto_casa, "CASA")
            g_ospite, img_visto_ospite = analizza_e_disegna_squadra(foto_ospite, "OSPITE")
            
            # Salviamo i dati nello stato per passarli al Box 2 (il pannello di modifica segreteria)
            st.session_state.casa_giocatori_input = g_casa
            st.session_state.ospite_giocatori_input = g_ospite
            st.session_state.dati_pronti = True
            
            # Mostriamo a schermo i due fogli con i rettangoli colorati per verificare i margini pixel
            st.success("Estrazione completata! Verifica qui sotto se le colonne geometriche (Rettangoli Blu/Verdi) sono centrate:")
            visto_col1, visto_col2 = st.columns(2)
            with visto_col1:
                st.image(img_visto_casa, caption="Mappa geometrica Squadra Casa", use_container_width=True)
            with visto_col2:
                st.image(img_visto_ospite, caption="Mappa geometrica Squadra Ospite", use_container_width=True)
