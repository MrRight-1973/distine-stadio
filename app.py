import streamlit as st
import json
import os
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Optional
from fpdf import FPDF

# 1. Definizione della struttura dati per il JSON con Pydantic
class Giocatore(BaseModel):
    numero: int = Field(description="Numero di riga o di maglia del giocatore")
    nome: str = Field(description="Cognome e Nome del giocatore")
    anno_nascita: int = Field(description="Anno di nascita a 4 cifre del giocatore")
    ruolo_speciale: Optional[str] = Field(None, description="Indica se Capitano (C) o Vice Capitano (V)")

class SquadraDati(BaseModel):
    nome_squadra: str = Field(description="Nome della squadra calcistica")
    allenatore: str = Field(description="Nome dell'allenatore principale")
    allenatore_seconda: Optional[str] = Field(None, description="Nome dell'allenatore in seconda, se presente")
    giocatori: List[Giocatore]

# 2. Funzione per l'estrazione dei dati tramite Gemini API
def analizza_distinta(immagine_pil):
    # Recupera la chiave API dai Secrets di Streamlit o dalle variabili d'ambiente
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("Chiave API di Gemini non trovata! Configurala nei Secrets di Streamlit con la voce GEMINI_API_KEY.")
        return None

    client = genai.Client(api_key=api_key)
    
    prompt = (
        "Analizza questa immagine di una distinta di gara di calcio. "
        "Estrai accuratamente il nome della squadra, il nome dell'allenatore, "
        "l'allenatore in seconda (se presente) e la lista di tutti i giocatori "
        "con il loro anno di nascita (calcolato o letto dalla data di nascita) "
        "e l'eventuale ruolo di capitano/vice."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=[immagine_pil, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SquadraDati,
                temperature=0.1
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Errore durante l'analisi con l'IA: {e}")
        return None

# 3. Funzione per la generazione del PDF tabellare
class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Report Estrazione Distinte di Gara", ln=True, align="C")
        self.ln(10)

def genera_pdf(squadre_dati):
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    for sq in squadre_dati:
        if not sq:
            continue
            
        # Sezione Squadra
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"Squadra: {sq['nome_squadra']}", ln=True)
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Allenatore: {sq['allenatore']}", ln=True)
        if sq.get('allenatore_seconda'):
            pdf.cell(0, 6, f"Allenatore in seconda: {sq['allenatore_seconda']}", ln=True)
        
        pdf.ln(5)
        
        # Tabella Giocatori
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(15, 7, "N°", border=1, align="C")
        pdf.cell(90, 7, "Cognome e Nome", border=1)
        pdf.cell(40, 7, "Anno di Nascita", border=1, align="C")
        pdf.cell(35, 7, "Note", border=1, align="C")
        pdf.ln()
        
        pdf.set_font("Helvetica", "", 10)
        for g in sq['giocatori']:
            ruolo = g.get('ruolo_speciale') or ""
            if ruolo == "C": ruolo = "Capitano"
            elif ruolo == "V": ruolo = "Vice Capitano"
            
            pdf.cell(15, 6, str(g['numero']), border=1, align="C")
            pdf.cell(90, 6, g['nome'], border=1)
            pdf.cell(40, 6, f"({g['anno_nascita']})", border=1, align="C")
            pdf.cell(35, 6, ruolo, border=1, align="C")
            pdf.ln()
            
        pdf.ln(15)
        
    return pdf.output()

# 4. Interfaccia utente Streamlit
st.set_page_config(page_title="Estrattore Distinte Calcio", layout="centered")

st.title("⚽ Estrattore Automatico Distinte di Gara")
st.write("Carica le foto o i PDF delle distinte per estrarre i dati dei giocatori e generare il report finale.")

# Controlla se la chiave è presente per guidare l'utente
if not st.secrets.get("GEMINI_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    st.info("💡 Ricordati di inserire la tua chiave `GEMINI_API_KEY` nei Secrets di Streamlit Sharing prima di procedere!")

# Upload dei file
file_squadra1 = st.file_uploader("Carica la distinta della Squadra 1", type=["png", "jpg", "jpeg"])
file_squadra2 = st.file_uploader("Carica la distinta della Squadra 2", type=["png", "jpg", "jpeg"])

if file_squadra1 and file_squadra2:
    if st.button("🚀 Avvia Estrazione e Genera PDF", type="primary"):
        squadre_risultati = []
        
        with st.spinner("L'intelligenza artificiale sta analizzando le distinte..."):
            img1 = Image.open(file_squadra1)
            dati1 = analizza_distinta(img1)
            if dati1:
                squadre_risultati.append(dati1)
                
            img2 = Image.open(file_squadra2)
            dati2 = analizza_distinta(img2)
            if dati2:
                squadre_risultati.append(dati2)
                
        if len(squadre_risultati) == 2:
            st.success("Estrazione completata con successo per entrambe le squadre!")
            
            # Anteprima a schermo
            for sq in squadre_risultati:
                with st.expander(f"📋 Anteprima {sq['nome_squadra']}"):
                    st.write(f"**Allenatore:** {sq['allenatore']}")
                    if sq.get('allenatore_seconda'):
                        st.write(f"**Allenatore in seconda:** {sq['allenatore_seconda']}")
                    st.dataframe(sq['giocatori'])
            
            # Generazione PDF
            pdf_bytes = genera_pdf(squadre_risultati)
            
            st.download_button(
                label="📥 Scarica Report PDF",
                data=pdf_bytes,
                file_name="report_distinte.pdf",
                mime="application/pdf"
            )
