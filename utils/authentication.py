# utils/authentication.py

import os
import sys
import time
import logging
import praw
import requests

logger = logging.getLogger(__name__)

# Variabili d'ambiente per l'autenticazione Reddit
USERAGENT = 'Bot for managing raffles on subreddits'
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
APP_REFRESH = os.getenv("APP_REFRESH")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

# Variabili d'ambiente per l'autenticazione Pastebin
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
PASTEBIN_USERNAME = os.getenv("PASTEBIN_USERNAME")
PASTEBIN_PASSWORD = os.getenv("PASTEBIN_PASSWORD")

def login_to_reddit():
    """Effettua il login a Reddit utilizzando le variabili d'ambiente."""
    return praw.Reddit(
        user_agent=USERAGENT,
        client_id=APP_ID,
        client_secret=APP_SECRET,
        refresh_token=APP_REFRESH,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD
    )

def connect_to_reddit(retries=5, delay=10):
    """Tenta di effettuare il login a Reddit con riprovi per resilienza."""
    for attempt in range(retries):
        try:
            reddit_instance = login_to_reddit()
            logger.info("Login a Reddit effettuato con successo.")
            return reddit_instance
        except Exception as e:
            logger.warning(f"Tentativo {attempt + 1} di login a Reddit fallito: {e}")
            time.sleep(delay)
    logger.error("Impossibile effettuare il login a Reddit dopo diversi tentativi. Uscita.")
    sys.exit(1)

def login_to_pastebin():
    """Effettua il login a Pastebin e recupera una chiave utente per l'API."""
    login_url = "https://pastebin.com/api/api_login.php"
    payload = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_user_name': PASTEBIN_USERNAME,
        'api_user_password': PASTEBIN_PASSWORD
    }
    try:
        response = requests.post(login_url, data=payload, timeout=10)
        response.raise_for_status()
        return response.text  # Restituisce la chiave utente se il login ha successo
    except Exception as e:
        logger.error(f"Impossibile effettuare il login a Pastebin: {e}")
        return None
