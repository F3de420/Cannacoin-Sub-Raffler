# handlers/subreddit_monitor.py

import time
import re
import logging

from utils.authentication import connect_to_reddit
from handlers.comment_handler import handle_comment

logger = logging.getLogger(__name__)

def monitor_subreddit(subreddit_name, data, delay=10):
    """Monitors a single subreddit for comments that trigger the raffle."""
    reddit_instance = connect_to_reddit()
    last_timestamp = data['last_processed_timestamps'].get(subreddit_name, 0)
    logger.info(f"Starting to monitor subreddit: {subreddit_name}")
    while True:
        try:
            subreddit = reddit_instance.subreddit(subreddit_name)
            for comment in subreddit.stream.comments(skip_existing=True):
                if comment.created_utc <= last_timestamp:
                    continue
                if comment.id in data["processed_posts"]:
                    logger.debug(f"Comment {comment.id} already processed. Skipping.")
                    continue
                match = re.search(handle_comment.TRIGGER, comment.body)
                if match:
                    handle_comment(comment, match, data)
                # Update the last processed timestamp and processed posts
                data['last_processed_timestamps'][subreddit_name] = max(
                    data['last_processed_timestamps'][subreddit_name],
                    comment.created_utc
                )
                data["processed_posts"].add(comment.id)
        except Exception as e:
            logger.error(f"Error in subreddit {subreddit_name}: {e}")
            time.sleep(delay)
