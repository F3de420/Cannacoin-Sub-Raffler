# utils/pastebin_helper.py

import logging
import requests
from utils.authentication import login_to_pastebin, PASTEBIN_API_KEY

logger = logging.getLogger(__name__)

def upload_to_pastebin(text, title):
    """Carica il testo su Pastebin e restituisce l'URL."""
    api_paste_code = text
    api_paste_name = title
    api_dev_key = PASTEBIN_API_KEY
    api_user_key = login_to_pastebin()
    if not api_user_key:
        return "Errore nel caricare la lista dei partecipanti su Pastebin."

    url = 'https://pastebin.com/api/api_post.php'
    data = {
        'api_dev_key': api_dev_key,
        'api_user_key': api_user_key,
        'api_option': 'paste',
        'api_paste_code': api_paste_code,
        'api_paste_name': api_paste_name,
        'api_paste_private': 1,  # Non in elenco
        'api_paste_expire_date': '1W'  # Scade in una settimana
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return response.text  # Restituisce l'URL del paste
    except Exception as e:
        logger.error(f"Impossibile caricare su Pastebin: {e}")
        return "Errore nel caricare la lista dei partecipanti su Pastebin."
