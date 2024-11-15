# bot.py

import threading
import time
import sys
import logging
from logging.handlers import RotatingFileHandler

from config.config import load_config, save_config, CONFIG_FILE
from utils.authentication import connect_to_reddit
from utils.spinner import spinner_animation
from handlers.subreddit_monitor import monitor_subreddit

# Logging configuration
log_handler = RotatingFileHandler("logs/bot.log", maxBytes=5 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

logger.info("Logging initialized.")

# Load configuration data
data = load_config()

# Global configurations
SUBREDDITS = data["config"]["subreddits"]

# Start the bot
if __name__ == "__main__":
    logger.info("Starting bot.")
    try:
        # Create an event to signal the spinner to stop
        spinner_stop_event = threading.Event()
        # Start the spinner in a separate thread
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
        logger.info("Bot stopped by user.")
        spinner_stop_event.set()
        spinner_thread.join()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        spinner_stop_event.set()
        spinner_thread.join()
        sys.exit(1)
