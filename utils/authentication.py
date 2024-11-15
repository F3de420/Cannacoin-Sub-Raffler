# utils/authentication.py

import os
import sys
import time
import logging
import praw
import requests

logger = logging.getLogger(__name__)

# Environment variables for Reddit authentication credentials
USERAGENT = 'Bot for managing raffles on subreddits'
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
APP_REFRESH = os.getenv("APP_REFRESH")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

# Environment variables for Pastebin authentication
PASTEBIN_API_KEY = os.getenv("PASTEBIN_API_KEY")
PASTEBIN_USERNAME = os.getenv("PASTEBIN_USERNAME")
PASTEBIN_PASSWORD = os.getenv("PASTEBIN_PASSWORD")

def login_to_reddit():
    """Log in to Reddit using environment variables."""
    return praw.Reddit(
        user_agent=USERAGENT,
        client_id=APP_ID,
        client_secret=APP_SECRET,
        refresh_token=APP_REFRESH,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD
    )

def connect_to_reddit(retries=5, delay=10):
    """Attempts to log in to Reddit with retries for resiliency."""
    for attempt in range(retries):
        try:
            reddit_instance = login_to_reddit()
            logger.info("Logged in to Reddit successfully.")
            return reddit_instance
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} to log in to Reddit failed: {e}")
            time.sleep(delay)
    logger.error("Failed to log in to Reddit after multiple attempts. Exiting.")
    sys.exit(1)

def login_to_pastebin():
    """Logs in to Pastebin and retrieves a user session key for API usage."""
    login_url = "https://pastebin.com/api/api_login.php"
    payload = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_user_name': PASTEBIN_USERNAME,
        'api_user_password': PASTEBIN_PASSWORD
    }
    try:
        response = requests.post(login_url, data=payload, timeout=10)
        response.raise_for_status()
        return response.text  # Returns the user session key if successful
    except Exception as e:
        logger.error(f"Failed to log in to Pastebin: {e}")
        return None
