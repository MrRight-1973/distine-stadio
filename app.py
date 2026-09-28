import streamlit as st
import json
import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Optional
from fpdf import FPDF

# Configurazione iniziale della pagina di Streamlit
st.set_page_config(page_title="Estrattore Distinte Calcio", page_icon="⚽", layout="wide")

# Schema dei dati strutturati richiesti a Gemini tramite Pydantic
class Giocatore(BaseModel):
    numero: int = Field(description="Numero progressivo o di maglia nella distinta")
    nome: str = Field(description="Cognome e Nome del giocatore")
    anno_nascita: int = Field(description="Anno di nascita a 4 cifre del giocatore")
    ruolo_speciale: Optional[str] = Field(None, description="Indica se Capitano (C) o Vice Capitano (V)")

class SquadraDati(BaseModel):
    nome_squadra: str = Field(description="Nome della squadra calcistica")
    allenatore: str = Field(description="Nome dell'allenatore principale")
    allenatore_seconda: Optional[str] = Field(None, description="Nome dell'allenatore in seconda, se presente")
    giocatori: List[Giocatore]

# Funzione per interrogare Gemini con gestione dei tentativi di rete (Anti-503)
def analizza_distinta_con_ia(immagine_pil, client):
    prompt = (
        "Analizza questa immagine di una distinta di gara di calcio. "
        "Estrai accuratamente il nome della squadra, il nome dell'allenatore, "
        "l'allenatore in seconda (se presente) e la lista di tutti i giocatori "
        "con il loro anno di nascita (calcolato o letto dalla data di nascita) "
        "e l'eventuale ruolo di capitano/vice."
    )
    
    # Utilizziamo esclusivamente il modello stabile di ultima generazione richiesto da Google
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
                    temperature=0.1  # Massima precisione nell'estrazione OCR
                ),
            )
            return json.loads(response.text)
            
        except APIError as e:
            # Gestione errore 503 (Server sovraccarico): aspetta e riprova
            if e.code == 503 and tentativo < massimi_tentativi - 1:
                time.sleep(2)
                continue
            else:
                raise e
        except Exception as e:
            raise e
            
    raise Exception("I server di Google sono temporaneamente occupati dal traffico. Riprova tra pochi istanti.")

# Classe per la strutturazione grafica del documento PDF tabellare
class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(31, 41, 55)
        self.cell(0, 10, "REPORT DISTINTE DI GARA", ln=True, align="C")
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
        pdf.set_text_color(29, 78, 216) # Titolo blu della squadra
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
        pdf.cell(40, 7, "Anno di Nascita", border=1, fill=True, align="C")
        pdf.cell(30, 7, "Note", border=1, fill=True, align="C")
        pdf.ln()
        
        # Riempimento dei dati estratti
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
st.title("⚽ Estrattore Automatico Distinte Calcio")
st.write("Carica le due immagini delle distinte per generare un unico report PDF strutturato.")

# Recupero della chiave API protetta tramite st.secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ Chiave API 'GEMINI_API_KEY' non trovata nei Secrets di Streamlit. Configurala nel pannello di controllo dell'app cloud.")
else:
    client = genai.Client(api_key=api_key)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distinta Squadra 1")
        file1 = st.file_uploader("Scegli la prima immagine", type=["png", "jpg", "jpeg"], key="f1")
    with col2:
        st.subheader("Distinta Squadra 2")
        file2 = st.file_uploader("Scegli la seconda immagine", type=["png", "jpg", "jpeg"], key="f2")
        
    if file1 and file2:
        if st.button("🚀 Analizza Distinte e Genera PDF", type="primary"):
            risultati = []
            errore_riscontrato = False
            
            with st.spinner("L'intelligenza artificiale sta leggendo le immagini..."):
                for i, file_caricato in enumerate([file1, file2], 1):
                    try:
                        img = Image.open(file_caricato)
                        dati_squadra = analizza_distinta_con_ia(img, client)
                        risultati.append(dati_squadra)
                        st.success(f"✅ Analizzata: {dati_squadra['nome_squadra']}")
                    except Exception as e:
                        st.error(f"❌ Errore durante l'analisi della distinta {i}: {str(e)}")
                        errore_riscontrato = True
                        
            if not errore_riscontrato and len(risultati) == 2:
                try:
                    pdf_bytes = genera_pdf(risultati)
                    st.write("")
                    st.download_button(
                        label="📥 Scarica il Report PDF",
                        data=pdf_bytes,
                        file_name="report_distinte_gara.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Errore nella compilazione grafica del file PDF: {e}")
