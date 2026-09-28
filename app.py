import streamlit as st
import pytesseract
import re
from PIL import Image
from fpdf import FPDF

# Configurazione iniziale della pagina di Streamlit
st.set_page_config(page_title="Estrattore Distinte PC", page_icon="⚽", layout="wide")

def analizza_testo_stampato(testo_grezzo):
    """Sfrutta la formattazione pulita del PC per dividere i dati"""
    squadra_dati = {
        "nome_squadra": "Squadra Rilevata",
        "allenatore": "Non rilevato",
        "allenatore_seconda": None,
        "giocatori": []
    }
    
    linee = [linea.strip() for linea in testo_grezzo.split('\n') if linea.strip()]
    giocatori_temporanei = []
    
    for i, linea in enumerate(linee):
        linea_lower = linea.lower()
        
        # 1. Trova l'allenatore
        if "allenatore" in linea_lower or "all." in linea_lower or "mr." in linea_lower:
            pope_all = linea.split(':')[-1].strip() if ':' in linea else linea
            if len(pope_all) > 3 and "allenatore" not in pope_all.lower():
                if squadra_dati["allenatore"] == "Non rilevato":
                    squadra_dati["allenatore"] = pope_all
                else:
                    squadra_dati["allenatore_seconda"] = pope_all
            continue
            
        # 2. Trova il nome della squadra (solitamente in cima e in maiuscolo)
        if i < 3 and len(linea) > 5 and linea.isupper() and "DISTINTA" not in linea:
            squadra_dati["nome_squadra"] = linea

        # 3. Estrazione dei giocatori cercando l'anno di nascita a 4 cifre
        anno_match = re.search(r'\b(19\d{2}|20\d{2})\b', linea)
        
        ruolo = None
        if "(c)" in linea_lower or "capitano" in linea_lower:
            ruolo = "(C)"
        elif "(v)" in linea_lower or "vice" in linea_lower:
            ruolo = "(V)"
            
        if anno_match:
            anno = int(anno_match.group(1))
            # Pulisce la riga per tenere solo il nome del giocatore
            nome_pulito = linea.replace(str(anno), '')
            nome_pulito = re.sub(r'\b\d{1,2}\b', '', nome_pulito) # Rimuove numeri di maglia isolati
            nome_pulito = re.sub(r'[^\w\s]', '', nome_pulito).strip() # Rimuove simboli residui
            
            if len(nome_pulito) > 3:
                giocatori_temporanei.append({
                    "nome": nome_pulito,
                    "anno_nascita": anno,
                    "ruolo_speciale": ruolo
                })

    # Assegna numerazione progressiva ordinata
    for idx, g in enumerate(giocatori_temporanei, 1):
        squadra_dati["giocatori"].append({
            "numero": idx,
            "nome": g["nome"],
            "anno_nascita": g["anno_nascita"],
            "ruolo_speciale": g["ruolo_speciale"]
        })
        
    return squadra_dati

# Struttura grafica del PDF finale scaricabile
class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(31, 41, 55)
        self.cell(0, 10, "REPORT AUTOMATICO DISTINTE", ln=True, align="C")
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
        pdf.set_text_color(29, 78, 216) # Colore Blu per la squadra
        pdf.cell(0, 10, sq["nome_squadra"].upper(), ln=True)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        all_2 = f" (Secondo: {sq['allenatore_seconda']})" if sq.get('allenatore_seconda') else ""
        pdf.cell(0, 6, f"Allenatore: {sq['allenatore']}{all_2}", ln=True)
        pdf.ln(4)
        
        # Tabella intestazione
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(243, 244, 246)
        pdf.cell(15, 7, "N°", border=1, fill=True, align="C")
        pdf.cell(100, 7, "Cognome e Nome", border=1, fill=True)
        pdf.cell(40, 7, "Anno Nascita", border=1, fill=True, align="C")
        pdf.cell(30, 7, "Note", border=1, fill=True, align="C")
        pdf.ln()
        
        # Righe Giocatori
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

# --- INTERFACCIA STREAMLIT ---
st.title("⚽ Estrattore Distinte Gratuito e Illimitato")
st.write("Sviluppato specificatamente per fogli stampati al PC. Nessun costo, nessuna chiave API, privacy garantita.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Distinta Squadra Casa")
    file1 = st.file_uploader("Carica modulo Casa", type=["png", "jpg", "jpeg"], key="c1")
with col2:
    st.subheader("Distinta Squadra Ospite")
    file2 = st.file_uploader("Carica modulo Ospite", type=["png", "jpg", "jpeg"], key="o1")
    
if file1 and file2:
    if st.button("🚀 Elabora e Genera PDF", type="primary"):
        risultati = []
        errore_rilevato = False
        
        with st.spinner("Lettura digitalizzata dei fogli in corso..."):
            for i, file_caricato in enumerate([file1, file2], 1):
                try:
                    img = Image.open(file_caricato)
                    testo_estratto = pytesseract.image_to_string(img, lang='ita')
                    
                    dati_squadra = analizza_testo_stampato(testo_estratto)
                    if dati_squadra["nome_squadra"] == "Squadra Rilevata":
                        dati_squadra["nome_squadra"] = f"Squadra {i}"
                        
                    risultati.append(dati_squadra)
                    st.success(f"✅ Letta con successo Distinta {i}")
                except Exception as e:
                    st.error(f"Errore sul file {i}: {e}")
                    errore_rilevato = True
                    
        if not errore_rilevato and len(risultati) == 2:
            try:
                pdf_output = genera_pdf(risultati)
                
                # RISOLUZIONE ERRORE: Convertiamo il bytearray in un oggetto bytes standard
                pdf_bytes = bytes(pdf_output)
                
                st.write("")
                st.download_button(
                    label="📥 Scarica il Report PDF della Partita",
                    data=pdf_bytes,
                    file_name="report_partita.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Errore durante la compilazione del PDF: {e}")
