import os
import re
import json
import requests
import logging
import threading
from bot import login, is_moderator
import concurrent.futures
import time
import itertools
from logging.handlers import RotatingFileHandler

# Logging configuration with rotating file handler
log_handler = RotatingFileHandler(
    "bot.log", maxBytes=5*1024*1024, backupCount=5
)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(log_handler)

CONFIG_FILE = "bot_config.json"
BACKUP_DIR = "backup"
TRIGGER = r'!raffle(?:\s+w\s*(\d+))?(?:\s+r\s*(\d+))?'
RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")

signature = (
    "\n\n---\n\n"
    "[Cannacoin Raffler](https://github.com/F3de420/Cannacoin-Sub-Raffler) | "
    "[r/StellarCannacoin](https://www.reddit.com/r/StellarCannaCoin/) | "
    "[r/StellarShroomz](https://www.reddit.com/r/StellarShroomz) | "
    "[StashApp](https://stashapp.cloud/) | "
    "[Cannacoin Discord](https://discord.gg/Xrpxm34QgW) | "
    "[Shroomz Discord](https://discord.gg/PXkKFKwZVA)"
)

# Global locks for thread safety
data_lock = threading.Lock()
raffle_lock = threading.Lock()
user_last_raffle = {}

# Load and save the configuration file
def load_data():
    """Loads data from the JSON file, creating defaults if file is missing."""
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
            "min_comment_karma": 10
        },
        "processed_posts": [],
        "last_processed_timestamp": 0
    }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    else:
        logging.warning("Configuration file missing. Using default data.")
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        data = default_data

    data["processed_posts"] = set(data["processed_posts"])
    return data

def save_data(data):
    """Saves data to JSON file."""
    data["processed_posts"] = list(data["processed_posts"])
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Initialize data and configurations
data = load_data()
PROCESSED_POSTS = data["processed_posts"]
SUBREDDITS = data["config"]["subreddits"]
EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
EXCLUDED_USERS = set(data["config"]["excluded_users"])
WHITELISTED_USERS = set(data["config"]["whitelisted_users"])
MAX_WINNERS = data["config"]["max_winners"]
MAX_REWARD = data["config"].get("max_reward", 1000)
MIN_REWARD = data["config"].get("min_reward", 10)
MIN_ACCOUNT_AGE = data["config"].get("min_account_age_days", 1) * 24 * 60 * 60  # Days to seconds
MIN_COMMENT_KARMA = data["config"].get("min_comment_karma", 10)
last_processed_timestamp = data["last_processed_timestamp"]

try:
    reddit = login()
except Exception as e:
    logging.error(f"Failed to log in to Reddit: {e}")
    exit(1)

def monitor_subreddit(subreddit_name):
    """Monitors a single subreddit for comments that trigger the raffle."""
    subreddit = reddit.subreddit(subreddit_name)
    logging.info(f"Monitoring subreddit: {subreddit_name}")
    global last_processed_timestamp
    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            with data_lock:  # Locks access to synchronize shared data
                if comment.created_utc <= last_processed_timestamp:
                    continue

                # Check for trigger command in comment
                if match := re.search(TRIGGER, comment.body):
                    author_name = comment.author.name
                    current_time = time.time()

                    # Flood control: 600 seconds (10 minutes) between commands from the same user
                    with raffle_lock:
                        if author_name in user_last_raffle:
                            last_raffle_time = user_last_raffle[author_name]
                            if current_time - last_raffle_time < 600:
                                logging.warning(f"Flood control triggered: User {author_name} attempted to start a raffle too soon.")
                                continue
                        # Update timestamp for last raffle command
                        user_last_raffle[author_name] = current_time

                    # Extracting `num_winners` and `reward` parameters
                    num_winners = max(1, min(int(match.group(1) or 1), MAX_WINNERS))
                    reward = max(0, min(int(match.group(2) or 0), MAX_REWARD))

                    handle_raffle(comment, num_winners, reward, subreddit_name)

                # Update `last_processed_timestamp` at a high frequency to reduce frequent I/O
                if time.time() - last_processed_timestamp > 5:  # Update every 5 seconds
                    last_processed_timestamp = max(last_processed_timestamp, comment.created_utc)
                    data["last_processed_timestamp"] = last_processed_timestamp
                    save_data(data)
    except Exception as e:
        logging.error(f"Error while monitoring subreddit {subreddit_name}: {e}")

def monitor_subreddits():
    """Starts a thread for each subreddit to monitor them concurrently."""
    logging.info("Starting subreddit monitoring...")
    spinner = itertools.cycle(['|', '/', '-', '\\'])

    # Limiting the ThreadPoolExecutor to a maximum of 4 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        while True:
            try:
                executor.map(monitor_subreddit, SUBREDDITS)
                time.sleep(1)
                print(f"Bot running... {next(spinner)}", end="\r")
                data["processed_posts"] = list(PROCESSED_POSTS)
                save_data(data)
            except Exception as e:
                logging.error(f"Unexpected error in monitoring loop: {e}")

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
        response.raise_for_status()
        return response.json().get("result", {}).get("random", {}).get("data", [])
    except Exception as e:
        logging.exception("Error in Random.org request. Using local random fallback.")
        import random
        return random.sample(range(min_val, max_val + 1), n)

def handle_raffle(trigger_comment, num_winners, reward, subreddit_name):
    """Handles the raffle process, excluding post and trigger authors."""
    author_name = trigger_comment.author.name
    post_author_name = trigger_comment.submission.author.name
    post_id = trigger_comment.submission.id

    # Only add to PROCESSED_POSTS if the raffle completes successfully
    if post_id in PROCESSED_POSTS:
        logging.info(f"Post {post_id} already processed. Ignoring.")
        trigger_comment.reply("A raffle has already been completed in this post." + signature)
        return

    if not (is_moderator(reddit, author_name, subreddit_name) or author_name in WHITELISTED_USERS):
        logging.warning(f"User {author_name} attempted unauthorized bot usage.")
        return

    # Limit the reward to be within the allowed range
    reward = max(min(reward, MAX_REWARD), MIN_REWARD)
    
    post = trigger_comment.submission
    post.comments.replace_more(limit=None)
    current_time = time.time()

    participants = {
        c.author.name for c in post.comments.list()
        if c.author and
        c.author.name not in EXCLUDED_BOTS and
        c.author.name != author_name and
        c.author.name != post_author_name and
        c.author.name not in EXCLUDED_USERS and
        (current_time - c.author.created_utc) >= MIN_ACCOUNT_AGE and
        c.author.comment_karma >= MIN_COMMENT_KARMA
    }

    if len(participants) < num_winners:
        trigger_comment.reply(f"Not enough participants to select {num_winners} winners." + signature)
        logging.info("Not enough participants for the raffle.")
        return

    PROCESSED_POSTS.add(post_id)
    data["processed_posts"] = list(PROCESSED_POSTS)
    save_data(data)

    winner_indices = get_random_numbers(num_winners, 0, len(participants) - 1)
    participants_list = list(participants)
    winners = [participants_list[i] for i in winner_indices]
    winners_text = '\n'.join(f"- u/{winner}" + (f" {reward} CANNACOIN" if reward > 0 else "") for winner in winners)
    participants_text = '\n'.join(f"- {participant}" for participant in participants_list)

    data["config"]["raffle_count"] += 1
    raffle_id = data["config"]["raffle_count"]
    save_data(data)

    eligibility_text = (
        f"\n\n**REQUIREMENTS**\n"
        f"- Comment Karma: {MIN_COMMENT_KARMA}\n"
        f"- Account Age (days): {int(MIN_ACCOUNT_AGE // (24 * 60 * 60))}"
    )
    prize_text = f"\nEach winner receives {reward} CANNACOIN." if reward > 0 else ""
    
    manual_reward_notice = (
        "\n\nNote: Rewards are distributed manually. "
        "Winners, please reply to this comment to arrange your reward."
    ) if reward > 0 else ""

    response_text = (
        f"**Raffle completed!**{prize_text}{eligibility_text}\n\n"
        f"**Qualified participants:**\n{participants_text}\n\n"
        f"**Winners:**\n{winners_text}\n\n"
        f"Thank you all for participating!{manual_reward_notice}\n\n"
        f"{signature}"
    )
    trigger_comment.reply(response_text)
    logging.info(f"Raffle completed in thread {post_id}. Winners: {winners} with reward: {reward}")

def backup_config():
    """Backup the configuration file every 6 hours."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    while True:
        time.sleep(21600)  # Every 6 hours
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{BACKUP_DIR}/bot_config_backup_{timestamp}.json"
        with data_lock:
            with open(CONFIG_FILE, "r") as original, open(backup_filename, "w") as backup:
                backup.write(original.read())
        logging.info(f"Backup saved as {backup_filename}")
        cleanup_old_backups(BACKUP_DIR, limit=10)

def cleanup_old_backups(directory, limit=10):
    backups = sorted(
        [f for f in os.listdir(directory) if f.startswith("bot_config_backup_")],
        key=lambda x: os.path.getmtime(os.path.join(directory, x))
    )
    for old_backup in backups[:-limit]:
        os.remove(os.path.join(directory, old_backup))
        logging.info(f"Old backup removed: {old_backup}")

def log_keep_alive():
    """Log every 30 minutes even if the bot is inactive."""
    while True:
        time.sleep(1800)  # 30 minutes
        logging.debug("Bot running, no activity in the last 30 minutes.")

if __name__ == "__main__":
    logging.info("Starting subreddit monitoring...")
    threading.Thread(target=backup_config, daemon=True).start()
    threading.Thread(target=log_keep_alive, daemon=True).start()
    monitor_subreddits()
