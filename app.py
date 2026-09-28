import streamlit as st
import re
from PIL import Image
import numpy as np
import easyocr
from fpdf import FPDF

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Estrattore Distinte Gratuito", page_icon="⚽", layout="wide")

# Inizializzazione del motore OCR locale per l'italiano (viene scaricato automaticamente al primo avvio)
@st.cache_resource
def carica_motore_ocr():
    # Carica i pesi per la lingua italiana ed inglese
    return easyocr.Reader(['it', 'en'], gpu=False)

reader = carica_motore_ocr()

def ripulisci_testo(testo):
    """Rimuove caratteri spuri comuni negli OCR grezzi"""
    return testo.strip().replace('|', '').replace('[', '').replace(']', '')

def analizza_testo_distinta(linee_testo):
    """
    Logica algoritmica per strutturare il testo estratto dall'OCR locale.
    Cerca pattern come numeri di maglia, anni a 4 cifre, capitani e allenatori.
    """
    squadra_dati = {
        "nome_squadra": "Squadra Rilevata",
        "allenatore": "Non rilevato",
        "allenatore_seconda": None,
        "giocatori": []
    }
    
    giocatori_temporanei = []
    
    for i, linea in enumerate(linee_testo):
        linea_pulita = ripulisci_testo(linea)
        linea_lower = linea_pulita.lower()
        
        # 1. Identificazione dell'Allenatore
        if "allenatore" in linea_lower or "all." in linea_lower or "mr." in linea_lower:
            # Prende la riga stessa o quella successiva se corta
            pope_all = linea_pulita.split(':')[-1].strip() if ':' in linea_pulita else linea_pulita
            if len(pope_all) > 3 and "allenatore" not in pope_all.lower():
                if squadra_dati["allenatore"] == "Non rilevato":
                    squadra_dati["allenatore"] = pope_all
                else:
                    squadra_dati["allenatore_seconda"] = pope_all
            continue
            
        # 2. Identificazione del Nome Squadra (spesso nelle prime righe in maiuscolo)
        if i < 4 and len(linea_pulita) > 8 and linea_pulita.isupper() and "DISTINTA" not in linea_pulita:
            squadra_dati["nome_squadra"] = linea_pulita
            
        # 3. Estrazione dei Giocatori tramite pattern
        # Cerca un anno a 4 cifre (es. 1998, 2004)
        anno_match = re.search(r'\b(19\d{2}|20\d{2})\b', linea_pulita)
        
        # Cerca se è indicata una nota di Capitano (C) o Vice (V)
        ruolo = None
        if "(c)" in linea_lower or "capitano" in linea_lower:
            ruolo = "(C)"
        elif "(v)" in linea_lower or "vice" in linea_lower:
            ruolo = "(V)"
            
        if anno_match:
            anno = int(anno_match.group(1))
            # Rimuove l'anno e i numeri isolati per isolare il nome del giocatore
            nome_pulito = linea_pulita.replace(str(anno), '')
            nome_pulito = re.sub(r'\b\d{1,2}\b', '', nome_pulito) # Rimuove numero maglia se attaccato
            nome_pulito = re.sub(r'[^\w\s]', '', nome_pulito).strip() # Rimuove parentesi residue
            
            if len(nome_pulito) > 3:
                giocatori_temporanei.append({
                    "nome": nome_pulito,
                    "anno_nascita": anno,
                    "ruolo_speciale": ruolo
                })
        else:
            # Fallback: se non trova l'anno ma la riga contiene chiaramente un nome e cognome in maiuscolo
            parole = linea_pulita.split()
            if len(parole) >= 2 and parole[0].isupper() and parole[1].isupper() and len(linea_pulita) > 5:
                if not any(k in linea_lower for k in ["allenatore", "dirigente", "arbitro", "societa"]):
                    giocatori_temporanei.append({
                        "nome": linea_pulita,
                        "anno_nascita": "N.D.",
                        "ruolo_speciale": ruolo
                    })

    # Assegna un numero progressivo ai giocatori individuati
    for idx, g in enumerate(giocatori_temporanei, 1):
        squadra_dati["giocatori"].append({
            "numero": idx,
            "nome": g["nome"],
            "anno_nascita": g["anno_nascita"],
            "ruolo_speciale": g["ruolo_speciale"]
        })
        
    return squadron_dati

# Classe personalizzata per esportare il PDF senza dipendenze cloud
class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(31, 41, 55)
        self.cell(0, 10, "REPORT AUTOMATICO DISTINTE DI GARA", ln=True, align="C")
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(156, 163, 175)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

def genera_pdf(dati_squadre):
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    for sq in dati_squadre:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(29, 78, 216)
        pdf.cell(0, 10, sq["nome_squadra"].upper(), ln=True)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        all_2 = f" (Secondo: {sq['allenatore_seconda']})" if sq.get('allenatore_seconda') else ""
        pdf.cell(0, 6, f"Allenatore: {sq['allenatore']}{all_2}", ln=True)
        pdf.ln(4)
        
        # Intestazione della tabella
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(243, 244, 246)
        pdf.cell(15, 7, "N°", border=1, fill=True, align="C")
        pdf.cell(100, 7, "Cognome e Nome", border=1, fill=True)
        pdf.cell(40, 7, "Anno Nascita", border=1, fill=True, align="C")
        pdf.cell(30, 7, "Note", border=1, fill=True, align="C")
        pdf.ln()
        
        # Righe dei giocatori
        pdf.set_font("Helvetica", "", 10)
        for g in sq["giocatori"]:
            ruolo = g.get("ruolo_speciale") if g.get("ruolo_speciale") else ""
            pdf.cell(15, 7, str(g["numero"]), border=1, align="C")
            pdf.cell(100, 7, g["nome"], border=1)
            pdf.cell(40, 7, str(g["anno_nascita"]), border=1, align="C")
            pdf.cell(30, 7, ruolo, border=1, align="C")
            pdf.ln()
            
        pdf.ln(10)
        
    return pdf.output()

# --- INTERFACCIA STREAMLIT UTENTE ---
st.title("⚽ Estrattore Distinte Domenicali (100% Locale e Gratuito)")
st.write("Questo strumento non usa chiavi API. Elabora i dati direttamente sul server in totale privacy.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Distinta Squadra di Casa")
    file1 = st.file_uploader("Carica immagine Casa", type=["png", "jpg", "jpeg"], key="home")
with col2:
    st.subheader("Distinta Squadra Ospite")
    file2 = st.file_uploader("Carica immagine Ospite", type=["png", "jpg", "jpeg"], key="away")
    
if file1 and file2:
    if st.button("🚀 Elabora e Genera PDF", type="primary"):
        risultati = []
        errore = False
        
        with st.spinner("Lettura dei moduli OCR in corso... (Il primo avvio potrebbe richiedere un minuto)"):
            for i, file_caricato in enumerate([file1, file2], 1):
                try:
                    # Converte il file Streamlit in un formato leggibile da EasyOCR
                    img = Image.open(file_caricato)
                    img_np = np.array(img)
                    
                    # Esegue la lettura del testo dall'immagine
                    ocr_risultato = reader.readtext(img_np, detail=0)
                    
                    # Converte le linee di testo grezze in un dizionario strutturato
                    dati_squadra = analizza_testo_distinta(ocr_risultato)
                    
                    # Forziamo un nome generico se l'OCR non ha letto il titolo in alto
                    if dati_squadra["nome_squadra"] == "Squadra Rilevata":
                        dati_squadra["nome_squadra"] = f"Squadra {i}"
                        
                    risultati.append(dati_squadra)
                    st.success(f"✅ Completata Distinta {i}: {dati_squadra['nome_squadra']}")
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione del file {i}: {e}")
                    errore = True
                    
        if not errore and len(risultati) == 2:
            try:
                pdf_bytes = genera_pdf(risultati)
                st.write("")
                st.download_button(
                    label="📥 Scarica il Report PDF della Domenica",
                    data=pdf_bytes,
                    file_name="distinte_domenica_calcio.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Errore nella generazione del file PDF: {e}")
