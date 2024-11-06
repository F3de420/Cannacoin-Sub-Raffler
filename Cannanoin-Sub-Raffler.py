import os
import re
import json
import requests
import logging
from bot import login, is_moderator
import concurrent.futures
import time  # Import required for periodic monitoring

# Logging configuration
logging.basicConfig(
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

CONFIG_FILE = "bot_config.json"
TRIGGER = r'!raffle\s*(\d*)'
RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")
CONFIG_LAST_MODIFIED = None  # Store last modification time of the config file

def load_data():
    """Loads data from the JSON config file, creating defaults if file is missing."""
    default_data = {
        "config": {
            "subreddits": ["MainSubreddit"],
            "max_winners": 5,
            "excluded_bots": ["AutoModerator", "timee_bot"],
            "excluded_users": [],
            "whitelisted_users": [],
            "raffle_count": 0
        },
        "processed_posts": [],
        "last_processed_timestamp": 0
    }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
        logging.warning("Configuration file missing. Using default data.")
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data

def save_data(data):
    """Saves data back to the JSON config file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def reload_data_if_changed():
    """Reloads the config file if it has been modified, updating global parameters."""
    global CONFIG_LAST_MODIFIED, data, SUBREDDITS, EXCLUDED_BOTS, EXCLUDED_USERS, WHITELISTED_USERS, MAX_WINNERS

    try:
        last_modified = os.path.getmtime(CONFIG_FILE)
        if CONFIG_LAST_MODIFIED is None or last_modified > CONFIG_LAST_MODIFIED:
            # Update the last modified timestamp and reload data
            CONFIG_LAST_MODIFIED = last_modified
            data = load_data()

            # Update global parameters with new data
            SUBREDDITS = data["config"]["subreddits"]
            EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
            EXCLUDED_USERS = set(data["config"]["excluded_users"])
            WHITELISTED_USERS = set(data["config"]["whitelisted_users"])
            MAX_WINNERS = data["config"]["max_winners"]

            logging.info("Configuration dynamically reloaded from file.")
            print("Configuration dynamically reloaded from file.")

    except Exception as e:
        logging.error(f"Error reloading configuration: {e}")

# Load initial configuration
data = load_data()
CONFIG_LAST_MODIFIED = os.path.getmtime(CONFIG_FILE)
PROCESSED_POSTS = set(data["processed_posts"])
SUBREDDITS = data["config"]["subreddits"]
EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
EXCLUDED_USERS = set(data["config"]["excluded_users"])
WHITELISTED_USERS = set(data["config"]["whitelisted_users"])
MAX_WINNERS = data["config"]["max_winners"]

reddit = login()

def monitor_subreddit(subreddit_name):
    """Monitors a single subreddit for comments that trigger the raffle."""
    subreddit = reddit.subreddit(subreddit_name)
    logging.info(f"Monitoring subreddit: {subreddit_name}")
    print(f"Monitoring subreddit: {subreddit_name}")
    for comment in subreddit.stream.comments(skip_existing=True):
        reload_data_if_changed()  # Check for config updates
        if comment.created_utc <= data["last_processed_timestamp"]:
            continue
        
        # Check for trigger command in comment
        if match := re.search(TRIGGER, comment.body):
            num_winners = int(match.group(1)) if match.group(1) else 1
            num_winners = min(num_winners, MAX_WINNERS)
            handle_raffle(comment, num_winners, subreddit_name)
            
        # Update the last processed timestamp
        data["last_processed_timestamp"] = max(data["last_processed_timestamp"], comment.created_utc)
        save_data(data)

def monitor_subreddits():
    """Starts a thread for each subreddit to monitor them concurrently."""
    print("Starting subreddit monitoring...")
    logging.info("Starting subreddit monitoring...")

    # List all subreddits being monitored at the start
    for subreddit_name in SUBREDDITS:
        print(f"Monitoring subreddit: {subreddit_name}")

    # Use ThreadPoolExecutor to monitor each subreddit concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            reload_data_if_changed()  # Check if there are any configuration changes
            executor.map(monitor_subreddit, SUBREDDITS)
            time.sleep(10)  # Check every 10 seconds

def get_random_numbers(n, min_val, max_val):
    """Fetches unique random numbers from Random.org, with a fallback to local random."""
    url = "https://api.random.org/json-rpc/2/invoke"
    headers = {"content-type": "application/json"}
    params = {
        "jsonrpc": "2.0",
        "method": "generateIntegers",
        "params": {
            "apiKey": RANDOM_ORG_API_KEY,
            "n": n,
            "min": min_val,
            "max": max_val,
            "replacement": False
        },
        "id": 42
    }
    try:
        response = requests.post(url, json=params, headers=headers)
        response.raise_for_status()  # Raises an exception for HTTP errors
        return response.json().get("result", {}).get("random", {}).get("data", [])
    except Exception as e:
        logging.exception("Error in Random.org request. Using local random fallback.")
        import random
        return random.sample(range(min_val, max_val + 1), n)

def handle_raffle(trigger_comment, num_winners, subreddit_name):
    """Handles the raffle process, excluding post and trigger authors."""
    author_name = trigger_comment.author.name
    post_author_name = trigger_comment.submission.author.name
    post_id = trigger_comment.submission.id

    # Check if the raffle has already been completed for this post
    if post_id in PROCESSED_POSTS:
        logging.info(f"Post {post_id} already processed. Ignoring.")
        trigger_comment.reply("A raffle has already been completed in this post.")
        return

    # Check if the user is either a moderator or in the whitelist
    if not (is_moderator(reddit, author_name, subreddit_name) or author_name in WHITELISTED_USERS):
        trigger_comment.reply("This bot is currently reserved for subreddit moderators and approved users.")
        logging.warning(f"User {author_name} attempted unauthorized bot usage.")
        print(f"User {author_name} attempted unauthorized bot usage.")
        return

    # Add post to processed posts and update configuration
    PROCESSED_POSTS.add(post_id)
    data["processed_posts"] = list(PROCESSED_POSTS)
    save_data(data)

    # Collect participants, excluding specific authors
    post = trigger_comment.submission
    post.comments.replace_more(limit=None)
    participants = {
        c.author.name for c in post.comments.list()
        if c.author and c.author.name not in EXCLUDED_BOTS
        and c.author.name != author_name
        and c.author.name != post_author_name
        and c.author.name not in EXCLUDED_USERS
    }

    # If there aren't enough participants, log and notify
    if len(participants) < num_winners:
        trigger_comment.reply(f"Not enough participants to select {num_winners} winners.")
        logging.info("Not enough participants for the raffle.")
        print("Not enough participants for the raffle.")
        return

    # Draw winners
    winner_indices = get_random_numbers(num_winners, 0, len(participants) - 1)
    participants_list = list(participants)
    winners = [participants_list[i] for i in winner_indices]
    winners_text = '\n'.join(f"- u/{winner}" for winner in winners)
    participants_text = '\n'.join(f"- {participant}" for participant in participants_list)

    # Increment raffle count
    data["config"]["raffle_count"] += 1
    save_data(data)

    # Signature with useful links
    signature = (
        "\n\n---\n\n"
        "[Cannacoin Raffler](https://github.com/F3de420/Cannacoin-Sub-Raffler) | "
        "[r/StellarCannacoin](https://www.reddit.com/r/StellarCannaCoin/) | "
        "[r/StellarShroomz](https://www.reddit.com/r/StellarShroomz) | "
        "[StashApp](https://stashapp.cloud/) | "
        "[Cannacoin Discord](https://discord.gg/Xrpxm34QgW) | "
        "[Shroomz Discord](https://discord.gg/PXkKFKwZVA)"
    )

    # Response text with winners, participants, and signature
    response_text = (
        f"**Raffle completed!**\n\n"
        f"**Qualified participants:**\n{participants_text}\n\n"
        f"**Winners:**\n{winners_text}\n\n"
        f"Thank you all for participating!\n\n"
        f"{signature}"
    )
    trigger_comment.reply(response_text)
    logging.info(f"Raffle completed in thread {post_id}. Winners: {winners}")
    print(f"Raffle completed in thread {post_id}. Winners: {winners}")

if __name__ == "__main__":
    logging.info("Starting subreddit monitoring...")
    print("Starting subreddit monitoring...")
    monitor_subreddits()
