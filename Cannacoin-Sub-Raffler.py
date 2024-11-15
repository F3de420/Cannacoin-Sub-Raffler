# Cannacoin-Sub-Raffler.py

import threading
import time
import sys
import logging
from logging.handlers import RotatingFileHandler

from config.config import load_config, save_config
from utils.authentication import connect_to_reddit
from utils.spinner import spinner_animation
from handlers.subreddit_monitor import monitor_subreddit

# Configurazione del logging
log_handler = RotatingFileHandler("logs/bot.log", maxBytes=5 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

logger.info("Logging inizializzato.")

# Carica i dati di configurazione
data = load_config()

# Configurazioni globali
SUBREDDITS = data["config"]["subreddits"]

# Avvia il bot
if __name__ == "__main__":
    logger.info("Avvio del bot.")
    try:
        # Crea un evento per segnalare allo spinner di fermarsi
        spinner_stop_event = threading.Event()
        # Avvia lo spinner in un thread separato
        spinner_thread = threading.Thread(target=spinner_animation, args=(spinner_stop_event,))
        spinner_thread.start()

        threads = []
        for subreddit in SUBREDDITS:
            thread = threading.Thread(target=monitor_subreddit, args=(subreddit, data), daemon=True)
            thread.start()
            threads.append(thread)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot interrotto dall'utente.")
        spinner_stop_event.set()
        spinner_thread.join()
    except Exception as e:
        logger.error(f"Si è verificato un errore imprevisto: {e}")
        spinner_stop_event.set()
        spinner_thread.join()
        sys.exit(1)
