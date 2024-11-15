# handlers/subreddit_monitor.py

import time
import re
import logging

from utils.authentication import connect_to_reddit
from handlers.comment_handler import handle_comment, TRIGGER

logger = logging.getLogger(__name__)

def monitor_subreddit(subreddit_name, data, delay=10):
    """Monitora un singolo subreddit per commenti che attivano il raffle."""
    reddit_instance = connect_to_reddit()
    last_timestamp = data['last_processed_timestamps'].get(subreddit_name, 0)
    logger.info(f"Inizio monitoraggio del subreddit: {subreddit_name}")
    while True:
        try:
            subreddit = reddit_instance.subreddit(subreddit_name)
            for comment in subreddit.stream.comments(skip_existing=True):
                if comment.created_utc <= last_timestamp:
                    continue
                if comment.id in data["processed_posts"]:
                    logger.debug(f"Commento {comment.id} già elaborato. Salto.")
                    continue
                match = re.search(TRIGGER, comment.body)
                if match:
                    handle_comment(comment, match, data, reddit_instance)
                # Aggiorna il timestamp dell'ultimo elaborato e i post elaborati
                data['last_processed_timestamps'][subreddit_name] = max(
                    data['last_processed_timestamps'][subreddit_name],
                    comment.created_utc
                )
                data["processed_posts"].add(comment.id)
        except Exception as e:
            logger.error(f"Errore nel subreddit {subreddit_name}: {e}")
            time.sleep(delay)

