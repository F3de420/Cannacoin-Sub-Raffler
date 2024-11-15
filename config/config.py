# config/config.py

import os
import json
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = "bot_config.json"

def load_config():
    """Loads configuration data from the JSON file."""
    logger.debug("Loading configuration data...")
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
            logger.debug(f"Configuration file {CONFIG_FILE} loaded successfully.")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {CONFIG_FILE}: {e}")
            data = default_data
            save_config(data)
    else:
        logger.warning("Configuration file missing. Creating a default configuration.")
        data = default_data
        save_config(data)

    # Initialize last_processed_timestamps for new subreddits
    for subreddit in data["config"]["subreddits"]:
        if subreddit not in data.get("last_processed_timestamps", {}):
            data["last_processed_timestamps"][subreddit] = 0

    data["processed_posts"] = set(data.get("processed_posts", []))
    return data

def save_config(data):
    """Saves the configuration data back to the JSON file."""
    logger.debug("Saving configuration data...")
    # Prepare a version of data suitable for saving
    data_to_save = {
        "config": data["config"],
        "processed_posts": list(data["processed_posts"]),  # Convert set to list for JSON compatibility
        "last_processed_timestamps": data["last_processed_timestamps"]
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
        logger.debug(f"Configuration saved to {CONFIG_FILE}.")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
