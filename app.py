import streamlit as st
import os
import json
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Optional
from fpdf import FPDF

# -------------------------------------------------------------------------
# 1. STRUTTURA DATI PYDANTIC (Forza Gemini a rispondere in JSON strutturato)
# -------------------------------------------------------------------------
class Giocatore(BaseModel):
    numero: int = Field(description="Numero di riga o di maglia nella distinta")
    nome: str = Field(description="Cognome e Nome del giocatore")
    anno_nascita: int = Field(description="Anno di nascita a 4 cifre del giocatore")
    ruolo_speciale: Optional[str] = Field(None, description="Indica se Capitano (C) o Vice Capitano (V)")

class SquadraDati(BaseModel):
    nome_squadra: str = Field(description="Nome della squadra calcistica")
    allenatore: str = Field(description="Nome dell'allenatore principale")
    allenatore_seconda: Optional[str] = Field(None, description="Nome dell'allenatore in seconda, se presente")
    giocatori: List[Giocatore]

# -------------------------------------------------------------------------
# 2. FUNZIONE ESTRAZIONE DATI CON GEMINI API
# -------------------------------------------------------------------------
def estrai_dati_distinta(uploaded_file, api_key: str) -> SquadraDati:
    """Invia l'immagine caricata a Gemini 2.5 Flash per l'estrazione dati."""
    # Inizializza il client con la chiave passata
    client = genai.Client(api_key=api_key)
    
    # Apri l'immagine tramite Pillow
    img = Image.open(uploaded_file)
    
    prompt = (
        "Analizza questa immagine di una distinta di gara di calcio. "
        "Estrai accuratamente il nome della squadra, il nome dell'allenatore, "
        "l'allenatore in seconda (se presente) e la lista di tutti i giocatori "
        "con il loro anno di nascita (calcolato o letto dalla data di nascita) "
        "e l'eventuale ruolo di capitano/vice."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[img, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SquadraDati,
            temperature=0.1
        ),
    )
    
    # Ritorna l'oggetto Pydantic validato caricando il JSON di risposta
    return SquadraDati.model_validate_json(response.text)

# -------------------------------------------------------------------------
# 3. FUNZIONE GENERAZIONE PDF REPORT
# -------------------------------------------------------------------------
class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.set_text_color(2, 117, 216) # Colore Blu principale
        self.cell(0, 10, "REPORT COMPLETO DISTINTE DI GARA", ln=True, align="C")
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

def genera_pdf_report(squadre: List[SquadraDati], output_path: str):
    """Crea un file PDF strutturato e pulito con i dati estratti."""
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    for sq in squadre:
        # Intestazione Squadra
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(240, 173, 78) # Colore Giallo/Arancio societario
        pdf.cell(0, 10, f"Squadra: {sq.nome_squadra.upper()}", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # Staff Tecnico
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 7, "Allenatore:", ln=False)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, sq.allenatore, ln=True)
        
        if sq.allenatore_seconda:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(40, 7, "Allenatore in Seconda:", ln=False)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 7, sq.allenatore_seconda, ln=True)
            
        pdf.ln(3)
        
        # Tabella Giocatori - Intestazione
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(15, 7, "N°", border=1, ln=False, align="C", fill=True)
        pdf.cell(90, 7, "Cognome e Nome", border=1, ln=False, fill=True)
        pdf.cell(40, 7, "Anno Nascita", border=1, ln=False, align="C", fill=True)
        pdf.cell(40, 7, "Note", border=1, ln=True, align="C", fill=True)
        
        # Righe Giocatori
        pdf.set_font("Arial", "", 10)
        for g in sq.giocatori:
            ruolo = g.ruolo_speciale if g.ruolo_speciale else "-"
            pdf.cell(15, 6, str(g.numero), border=1, ln=False, align="C")
            pdf.cell(90, 6, g.nome, border=1, ln=False)
            pdf.cell(40, 6, str(g.anno_nascita), border=1, ln=False, align="C")
            pdf.cell(40, 6, ruolo, border=1, ln=True, align="C")
            
        pdf.ln(10) # Spazio tra le due squadre
        
    pdf.output(output_path)

# -------------------------------------------------------------------------
# 4. INTERFACCIA UTENTE STREAMLIT (Web UI)
# -------------------------------------------------------------------------
st.set_page_config(page_title="Estrattore Distinte Calcio", layout="centered")

st.title("⚽ Estrattore Distinte Calcio con AI")
st.write("Carica le due immagini delle distinte per estrarre l'elenco dei giocatori e generare un PDF riassuntivo.")

# Sidebar per la configurazione della chiave API
st.sidebar.header("Configurazione")
api_key = st.sidebar.text_input("Inserisci la tua Gemini API Key:", type="password")
st.sidebar.markdown("[Come ottenere una API Key gratuita](https://aistudio.google.com/)")

if not api_key:
    st.info("Per favore, inserisci la tua Gemini API Key nella barra laterale per iniziare.")
else:
    # Selezione file (Massimo 2 file contemporaneamente)
    st.subheader("1. Carica i file delle distinte")
    uploaded_files = st.file_uploader(
        "Seleziona esattamente 2 immagini (PNG, JPG, JPEG)", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if len(uploaded_files) != 2:
            st.warning("Per favore, seleziona esattamente 2 file per procedere al confronto completo.")
        else:
            st.success("File caricati correttamente!")
            
            # Bottone di avvio processo
            if st.button("🚀 Avvia Estrazione e Genera PDF"):
                squadre_estratte = []
                
                # Progress bar per il feedback visivo
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Elaborazione del file {idx+1}: {file.name}...")
                    try:
                        dati_squadra = estrai_dati_distinta(file, api_key)
                        squadre_estratte.append(dati_squadra)
                        
                        # Mostra un'anteprima dei dati estratti nell'interfaccia
                        with st.expander(f"Visualizza anteprima: {dati_squadra.nome_squadra}"):
                            st.write(f"**Allenatore:** {dati_squadra.allenatore}")
                            st.write(f"**Giocatori trovati:** {len(dati_squadra.giocatori)}")
                            st.dataframe(dati_squadra.giocatori)
                            
                    except Exception as e:
                        st.error(f"Errore durante la lettura di {file.name}: {e}")
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("Generazione del report PDF in corso...")
                
                if len(squadre_estratte) == 2:
                    pdf_filename = "report_distinte_gara.pdf"
                    try:
                        genera_pdf_report(squadre_estratte, pdf_filename)
                        
                        # Bottone di download del file PDF generato
                        st.success("✨ Report PDF generato con successo!")
                        with open(pdf_filename, "rb") as f:
                            st.download_button(
                                label="📥 Scarica Report PDF",
                                data=f,
                                file_name=pdf_filename,
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Errore nella creazione del PDF: {e}")
                else:
                    st.error("Impossibile generare il PDF. Uno o entrambi i file hanno riscontrato errori.")
