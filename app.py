import streamlit as tf
import base64
import json
from openai import OpenAI

# 1. Configurazione della pagina Streamlit
st.set_page_config(page_title="Estrattore Distinte Calcio", page_icon="⚽", layout="centered")

st.title("⚽ Estrattore Automatico Distinte Gara")
st.write("Carica la foto o il PDF della distinta LND per estrarre istantaneamente i giocatori e l'anno di nascita.")

# 2. Inizializzazione del client OpenAI
# Su Streamlit Cloud la chiave viene letta in automatico dai "Secrets" della piattaforma
client = OpenAI()

def encode_image(uploaded_file):
    """Converte il file caricato dall'utente in stringa Base64 per le API"""
    bytes_data = uploaded_file.getvalue()
    return base64.b64encode(bytes_data).decode('utf-8')

# 3. Interfaccia di caricamento file
file_caricato = st.file_uploader("Trascina qui la foto della distinta o selezionala dal dispositivo", type=["png", "jpg", "jpeg"])

if file_caricato is not None:
    # Mostra l'anteprima dell'immagine caricata nella Web App
    st.image(file_caricato, caption="Distinta caricata correttamente", use_column_width=True)
    
    # Pulsante per avviare l'elaborazione
    if st.button("🚀 Estrai Giocatori"):
        with st.spinner("L'Intelligenza Artificiale sta leggendo la distinta... Attendi qualche secondo."):
            try:
                # Conversione e preparazione del prompt
                base64_image = encode_image(file_caricato)
                
                prompt_sistema = (
                    "Sei un assistente specializzato nell'estrazione dati da documenti sportivi. "
                    "Estrai la lista di tutti i GIOCATORI presenti nella distinta. "
                    "Per ogni giocatore trova: Nome, Cognome e Anno di Nascita. "
                    "Ignora dirigenti, arbitri e allenatori. "
                    "Rispondi ESCLUSIVAMENTE con un oggetto JSON avente una chiave 'giocatori' che contiene la lista. "
                    "Esempio format: { 'giocatori': [ {'cognome_nome': 'ROSSI ANDREA', 'anno_nascita': 2005} ] }"
                )
                
                # Chiamata API
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={ "type": "json_object" },
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Estrai i dati dei calciatori da questa immagine."},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    temperature=0.0
                )
                
                # Elaborazione del risultato JSON
                risultato_testo = response.choices.message.content
                dati_json = json.loads(risultato_testo)
                lista_giocatori = dati_json.get("giocatori", [])
                
                if lista_giocatori:
                    st.success("✅ Estrazione completata con successo!")
                    
                    # Mostra i dati in una bellissima tabella interattiva nativa di Streamlit
                    st.subheader("📋 Elenco Giocatori Estratti")
                    st.dataframe(lista_giocatori, use_container_width=True)
                    
                    # Permette all'utente di copiare i dati in formato testo strutturato
                    testo_formattato = ""
                    for g in lista_giocatori:
                        testo_formattato += f"{g['cognome_nome']} - {g['anno_nascita']}\n"
                    st.text_area("Copia l'elenco veloce da qui:", value=testo_formattato, height=200)
                else:
                    st.warning("Nessun giocatore trovato nell'immagine. Verifica che il foglio sia leggibile.")
                    
            except Exception as e:
                st.error(f"Si è verificato un errore durante l'elaborazione: {e}")
