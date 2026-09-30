import base64
import io
import re
from PIL import Image

def pulisci_testo(testo):
    """Rimuove i caratteri speciali come _ e converte tutto in MAIUSCOLO."""
    if not testo or str(testo).strip() == "":
        return ""
    testo_pulito = str(testo).replace("_", " ")
    testo_pulito = re.sub(r'\s+', ' ', testo_pulito)
    return testo_pulito.strip().upper()

def encode_image(uploaded_file):
    """Apre l'immagine, la ridimensiona e la converte in stringa Base64 per l'API."""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1600, 1600))
    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=85)
    return base64.b64encode(buffer_img.getvalue()).decode('utf-8')
