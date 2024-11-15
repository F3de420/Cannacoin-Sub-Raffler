import os
import sys
import json
import logging
import threading
import time
import re
import requests
import random
import praw
import itertools
from logging.handlers import RotatingFileHandler

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

# Random.org API Key
RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")

# Logging configuration
log_handler = RotatingFileHandler("bot.log", maxBytes=5 * 1024 * 1024, backupCount=5)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

logger.info("Logging initialized.")

# Global variables and configuration
CONFIG_FILE = "bot_config.json"
TRIGGER = r'!raffle4canna(?:\s+w\s*(\d+))?(?:\s+r\s*([\d;]+))?'

signature = (
    "\n\n---\n\n"
    "[Cannacoin Raffler](https://github.com/F3de420/Cannacoin-Sub-Raffler) | "
    "[r/StellarCannaCoin](https://www.reddit.com/r/StellarCannaCoin/) | "
    "[r/StellarShroomz](https://www.reddit.com/r/StellarShroomz) | "
    "[StashApp](https://stashapp.cloud/) | "
    "[Cannacoin Discord](https://discord.gg/Xrpxm34QgW) | "
    "[Shroomz Discord](https://discord.gg/PXkKFKwZVA)"
)

def login():
    """Log in to Reddit using environment variables."""
    return praw.Reddit(
        user_agent=USERAGENT,
        client_id=APP_ID,
        client_secret=APP_SECRET,
        refresh_token=APP_REFRESH,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD
    )

def is_moderator(reddit_instance, username, subreddit_name):
    """Checks whether the user is a moderator of the specified subreddit."""
    subreddit = reddit_instance.subreddit(subreddit_name)
    moderators = subreddit.moderator()
    return username in [mod.name for mod in moderators]

def login_pastebin():
    """Logs in to Pastebin and retrieves a user session key for API usage."""
    login_url = "https://pastebin.com/api/api_login.php"
    payload = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_user_name': PASTEBIN_USERNAME,
        'api_user_password': PASTEBIN_PASSWORD
    }
    response = requests.post(login_url, data=payload, timeout=10)
    response.raise_for_status()
    return response.text  # Returns the user session key if successful

# Function to load data
def load_data():
    """Loads data from the JSON file, creating defaults if the file is missing."""
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
            save_data(data)
    else:
        logger.warning("Configuration file missing. Creating a default configuration.")
        data = default_data
        save_data(data)

    # Initialize last_processed_timestamps for new subreddits
    for subreddit in data["config"]["subreddits"]:
        if subreddit not in data.get("last_processed_timestamps", {}):
            data["last_processed_timestamps"][subreddit] = 0

    data["processed_posts"] = set(data.get("processed_posts", []))
    return data

# Function to save data
def save_data(data):
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

# Initialize data and configurations
data = load_data()

# Global configurations derived from the file
PROCESSED_POSTS = data["processed_posts"]
SUBREDDITS = data["config"]["subreddits"]
EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
EXCLUDED_USERS = set(data["config"]["excluded_users"])
WHITELISTED_USERS = set(data["config"]["whitelisted_users"])
MAX_WINNERS = data["config"]["max_winners"]
MAX_REWARD = data["config"].get("max_reward", 1000)
MIN_REWARD = data["config"].get("min_reward", 10)
MIN_ACCOUNT_AGE = data["config"].get("min_account_age_days", 1) * 24 * 60 * 60  # Days in seconds
MIN_COMMENT_KARMA = data["config"].get("min_comment_karma", 10)
DEUSEX_USERNAME = data["config"]["deusexmachina"]

# Connect to Reddit
def connect_to_reddit(retries=5, delay=10):
    """Attempts to log in to Reddit with retries for resiliency."""
    for attempt in range(retries):
        try:
            reddit_instance = login()
            logger.info("Logged in to Reddit successfully.")
            return reddit_instance
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} to log in to Reddit failed: {e}")
            time.sleep(delay)
    logger.error("Failed to log in to Reddit after multiple attempts. Exiting.")
    sys.exit(1)

# Function to monitor subreddit
def monitor_subreddit(subreddit_name, delay=10):
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
                if re.search(TRIGGER, comment.body):
                    handle_comment(comment, re.search(TRIGGER, comment.body))
                # Update the last processed timestamp and processed posts
                data['last_processed_timestamps'][subreddit_name] = max(
                    data['last_processed_timestamps'][subreddit_name],
                    comment.created_utc
                )
                data["processed_posts"].add(comment.id)
                save_data(data)
        except Exception as e:
            logger.error(f"Error in subreddit {subreddit_name}: {e}")
            time.sleep(delay)

# Function to handle comments
def handle_comment(comment, match):
    """Handles the comment processing and validation based on trigger pattern."""
    author_name = comment.author.name
    subreddit_name = comment.subreddit.display_name

    # Check if the comment has already been processed
    if comment.id in data["processed_posts"]:
        logger.debug(f"Comment {comment.id} already processed. Skipping.")
        return

    # Extract parameters from the trigger
    num_winners = int(match.group(1)) if match.group(1) else 1
    rewards = [int(r) for r in match.group(2).split(";")] if match.group(2) else [0]

    # Ensure that the number of rewards matches the number of winners
    assigned_rewards = [
        rewards[i] if i < len(rewards) else rewards[-1] for i in range(num_winners)
    ]

    # Calculate the total reward
    total_reward = sum(assigned_rewards) if any(assigned_rewards) else 0

    # Get the list of participants
    participants = [
        c.author.name for c in comment.submission.comments.list()
        if c.author and
        c.author.name not in EXCLUDED_BOTS and
        c.author.name not in EXCLUDED_USERS and
        c.author.name != author_name  # Exclude the raffle initiator
    ]

    # Remove duplicates
    participants = list(set(participants))

    # Verify if there are enough participants
    if len(participants) < num_winners:
        logger.warning(f"Not enough participants for raffle by u/{author_name}")
        try:
            comment.reply(
                f"**Error:** Not enough participants to complete the raffle.\n\n"
                f"**Participants Needed:** {num_winners}, but only {len(participants)} were found."
            )
        except Exception as e:
            logger.error(f"Failed to post error response: {e}")
        return

    # Select winners using Random.org
    winners = select_winners_with_random_org(participants, num_winners)
    if not winners:
        # Fallback using the random module
        logger.warning("Random.org not available, using the random module as fallback.")
        winners = random.sample(participants, num_winners)

    # Construct the winners message
    if total_reward == 0:
        # Case when rewards are zero
        results_message = "\n".join([
            f"{i+1}. u/{winner}" for i, winner in enumerate(winners)
        ])
        final_note = ""  # No final note
    else:
        results_message = "\n".join([
            f"{i+1}. u/{winner} - {assigned_rewards[i]} CANNACOIN" for i, winner in enumerate(winners)
        ])
        final_note = (
            "\n\n**Note:** All prizes will be distributed manually. "
            "Winners, please reply to this comment with your Cannacoin wallet address to claim your rewards. "
            "Thank you for participating!"
        )

    logger.info(f"Winners selected: {winners}")

    # Upload participants to Pastebin
    pastebin_link = None
    try:
        participants_formatted = ' | '.join(participants)
        pastebin_link = upload_to_pastebin(
            participants_formatted,
            title=f"Raffle Participants: {comment.submission.id}"
        )
        # Modify the link to point to the raw version
        if 'pastebin.com/' in pastebin_link:
            pastebin_key = pastebin_link.split('/')[-1]
            pastebin_raw_link = f"https://pastebin.com/raw/{pastebin_key}"
        else:
            pastebin_raw_link = pastebin_link
        logger.info(f"Participants uploaded to Pastebin: {pastebin_raw_link}")
    except Exception as e:
        logger.error(f"Failed to upload participants to Pastebin: {e}")
        pastebin_raw_link = "Error uploading participants list to Pastebin."

    # Construct the bot's response
    response = f"**Raffle Completed!**\n\n"
    response += f"**Total Participants:** {len(participants)}\n"
    response += f"[Full List of Eligible Participants]({pastebin_raw_link})\n\n"
    if total_reward > 0:
        response += f"**Total Reward Pool:** {total_reward} CANNACOIN\n\n"
    response += f"**Winners:**\n{results_message}\n\n"
    response += "---\n\n"
    response += "Thank you all for participating!\n\n"
    response += final_note + "\n\n"
    response += signature

    # Reply to the comment
    try:
        comment.reply(response)
        logger.info(f"Posted results successfully in thread: {comment.submission.id}")
    except Exception as e:
        logger.error(f"Failed to post results: {e}")

    # Add the comment to processed posts and save data
    data["processed_posts"].add(comment.id)
    save_data(data)

# Function to select winners using Random.org
def select_winners_with_random_org(participants, num_winners):
    """Selects winners using Random.org API."""
    try:
        api_url = 'https://api.random.org/json-rpc/4/invoke'
        headers = {'Content-Type': 'application/json'}
        data = {
            'jsonrpc': '2.0',
            'method': 'generateIntegers',
            'params': {
                'apiKey': RANDOM_ORG_API_KEY,
                'n': num_winners,
                'min': 0,
                'max': len(participants) - 1,
                'replacement': False
            },
            'id': random.randint(1, 100000)
        }
        response = requests.post(api_url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        random_data = response.json()

        if 'error' in random_data:
            logger.error(f"Error from Random.org: {random_data['error']}")
            return None

        indices = random_data['result']['random']['data']
        winners = [participants[i] for i in indices]
        return winners
    except Exception as e:
        logger.error(f"Failed to obtain random numbers from Random.org: {e}")
        return None

# Function to upload text to Pastebin
def upload_to_pastebin(text, title):
    """Uploads text to Pastebin and returns the URL."""
    api_paste_code = text
    api_paste_name = title
    api_dev_key = PASTEBIN_API_KEY
    api_user_key = login_pastebin()

    url = 'https://pastebin.com/api/api_post.php'
    data = {
        'api_dev_key': api_dev_key,
        'api_user_key': api_user_key,
        'api_option': 'paste',
        'api_paste_code': api_paste_code,
        'api_paste_name': api_paste_name,
        'api_paste_private': 1,  # Unlisted
        'api_paste_expire_date': '1W'  # Expires in one week
    }
    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()
    return response.text  # Returns the URL of the paste

# Spinner function
def spinner_animation(stop_event):
    """Displays a spinner animation in the console."""
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    while not stop_event.is_set():
        sys.stdout.write('\r' + next(spinner) + ' Bot is running...')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\rBot stopped.            \n')
    sys.stdout.flush()

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
            thread = threading.Thread(target=monitor_subreddit, args=(subreddit,), daemon=True)
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
