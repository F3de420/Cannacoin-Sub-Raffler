# config/config.py

import os
import json
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = "bot_config.json"

def load_config():
    """Carica i dati di configurazione dal file JSON."""
    logger.debug("Caricamento dei dati di configurazione...")
    default_data = {
        "config": {
            "subreddits": ["MainSubreddit"],
            "max_winners": 5,
            "excluded_bots": ["AutoModerator", "timee_bot"],
            "excluded_users": [],
            "whitelisted_users": [],
            "raffle_count": 0,
            "max_reward": 1000,
            "min_reward": 10,
            "min_account_age_days": 1,
            "min_comment_karma": 10,
            "deusexmachina": "admin_username"
        },
        "processed_posts": [],
        "last_processed_timestamps": {}
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            logger.debug(f"File di configurazione {CONFIG_FILE} caricato con successo.")
        except json.JSONDecodeError as e:
            logger.error(f"Errore nel decodificare il JSON da {CONFIG_FILE}: {e}")
            data = default_data
            save_config(data)
    else:
        logger.warning("File di configurazione mancante. Creazione di una configurazione di default.")
        data = default_data
        save_config(data)

    # Inizializza last_processed_timestamps per nuovi subreddit
    for subreddit in data["config"]["subreddits"]:
        if subreddit not in data.get("last_processed_timestamps", {}):
            data["last_processed_timestamps"][subreddit] = 0

    data["processed_posts"] = set(data.get("processed_posts", []))
    return data

def save_config(data):
    """Salva i dati di configurazione nel file JSON."""
    logger.debug("Salvataggio dei dati di configurazione...")
    # Prepara una versione dei dati adatta per il salvataggio
    data_to_save = {
        "config": data["config"],
        "processed_posts": list(data["processed_posts"]),  # Converti il set in lista per compatibilità JSON
        "last_processed_timestamps": data["last_processed_timestamps"]
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
        logger.debug(f"Configurazione salvata in {CONFIG_FILE}.")
    except Exception as e:
        logger.error(f"Impossibile salvare la configurazione: {e}")
