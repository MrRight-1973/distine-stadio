import streamlit as st
import requests
import json

def pubblica_distinta_esterna(pacchetto_gara):
    """
    Invia i dati della distinta a un contenitore JSON gratuito online 
    e restituisce il link della pagina HTML pulita per i tifosi.
    """
    # Utilizziamo il servizio gratuito e immediato jsonbin.io o un semplice kv bucket.
    # Per farlo senza account istantaneamente, usiamo un server di test pubblico (es. jsonbin o kv)
    # In alternativa creiamo una struttura HTML pronta che la segreteria può visualizzare.
    
    try:
        # Salviamo la distinta online per la lettura mobile
        url_storage = "https://jsonbin.io"
        headers = {
            "Content-Type": "application/json",
            "X-Master-Key": "$2a$10$ExmpLeKeyHeresiGnaLDoNotCopy" # Sostituibile con una chiave gratuita o rimpiazzabile con file statico
        }
        
        # In alternativa, per non dipendere da chiavi API complesse, generiamo direttamente 
        # un file HTML pronto che puoi salvare nel tuo repository GitHub Pages!
        html_puro = genera_html_tifosi(pacchetto_gara)
        
        return html_puro
    except Exception as e:
        st.error(f"Errore nella pubblicazione esterna: {e}")
        return None

def genera_html_tifosi(dati):
    """Genera il codice HTML puro, leggerissimo e senza loghi per lo smartphone del tifoso"""
    info = dati.get("info_gara", {})
    casa = dati.get("casa", {})
    ospite = dati.get("ospite", {})
    
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚽ Distinta Live - Azzurra Due Carrare</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #F0F4F8; margin: 0; padding: 15px; color: #2D3748; }}
        .titolo-match {{ text-align: center; color: #1A365D; font-size: 24px; font-weight: bold; margin-bottom: 5px; }}
        .sottotitolo {{ text-align: center; color: #2B6CB0; font-size: 16px; font-weight: bold; margin-bottom: 5px; }}
        .info-match {{ text-align: center; color: #4A5568; font-size: 13px; margin-bottom: 20px; line-height: 1.4; }}
        .card-squadra {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px; }}
        .nome-squadra {{ color: #2B6CB0; font-size: 18px; font-weight: bold; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; margin-bottom: 10px; }}
        .allenatore {{ font-style: italic; color: #4A5568; font-size: 13px; margin-bottom: 10px; }}
        .riga-giocatore {{ display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #EDF2F7; font-size: 15px; }}
        .num-maglia {{ font-weight: bold; color: #2B6CB0; width: 25px; }}
        .nome-giocatore {{ flex-grow: 1; text-align: left; padding-left: 5px; color: #2D3748; }}
        .anno-giocatore {{ color: #A0AEC0; width: 40px; text-align: right; }}
        .footer-stadio {{ text-align: center; margin-top: 25px; color: #A0AEC0; font-size: 12px; padding: 10px 0; }}
    </style>
</head>
<body>
    <div class="titolo-match">⚽ AZZURRA DUE CARRARE</div>
    <div class="sottotitolo">DISTINTA DIGITALE LIVE</div>
    <div class="info-match">🏆 {info.get('campionato', '')} | 📅 {info.get('data', '')}<br>🏁 Arbitro: {info.get('arbitro', '')}</div>

    <!-- SQUADRA CASA -->
    <div class="card-squadra">
        <div class="nome-squadra">🏠 {casa.get('squadra', 'SQUADRA CASA')}</div>
        <div class="allenatore">All. {casa.get('allenatore', '')}</div>
    """
    
    for g in casa.get("giocatori", []):
        if g.get("GIOCATORE", "").strip():
            html += f"""
        <div class="riga-giocatore">
            <span class="num-maglia">{g.get('N°', '')}</span>
            <span class="nome-giocatore">{g.get('GIOCATORE', '')}</span>
            <span class="anno-giocatore">{g.get('ANNO', '')}</span>
        </div>"""
            
    html += f"""
    </div>

    <!-- SQUADRA OSPITE -->
    <div class="card-squadra">
        <div class="nome-squadra">🚀 {ospite.get('squadra', 'SQUADRA OSPITE')}</div>
        <div class="allenatore">All. {ospite.get('allenatore', '')}</div>
    """
    
    for g in ospite.get("giocatori", []):
        if g.get("GIOCATORE", "").strip():
            html += f"""
        <div class="riga-giocatore">
            <span class="num-maglia">{g.get('N°', '')}</span>
            <span class="nome-giocatore">{g.get('GIOCATORE', '')}</span>
            <span class="anno-giocatore">{g.get('ANNO', '')}</span>
        </div>"""
            
    html += """
    </div>
    <div class="footer-stadio">⚽ Azzurra Due Carrare - Aggiornato in tempo reale</div>
</body>
</html>
"""
    return html
