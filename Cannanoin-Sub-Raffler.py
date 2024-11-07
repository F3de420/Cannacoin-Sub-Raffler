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
import random
import sys
from logging.handlers import RotatingFileHandler

# Logging configuration with log rotation
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = RotatingFileHandler("bot.log", maxBytes=5*1024*1024, backupCount=2)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

CONFIG_FILE = "bot_config.json"
TRIGGER = r'^!raffle(?:\s+w\s+(\d+))?(?:\s+r\s+(\d+))?$'
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

# Constants
DELETED_USER = "[deleted]"

# Lock for synchronizing access to shared data
data_lock = threading.Lock()
# Lock for rate limiting invalid command responses
rate_limit_lock = threading.Lock()
invalid_command_timestamps = {}

def load_data():
    """
    Loads data from the JSON configuration file. If the file does not exist, creates default data.

    Returns:
        dict: Configuration data loaded from the file or default data.
    """
    default_data = {
        "config": {
            "subreddits": ["MainSubreddit"],
            "max_winners": 5,
            "max_reward": 100,
            "min_reward": 1000,
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
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error("Configuration file is corrupted. Using default data.")
                return default_data
    else:
        logger.warning("Configuration file missing. Using default data.")
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data

def save_data(data):
    """
    Saves data to the JSON configuration file with thread-safe access.

    Args:
        data (dict): The data to save.
    """
    with data_lock:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

data = load_data()
with data_lock:
    PROCESSED_POSTS = set(data["processed_posts"])
    SUBREDDITS = data["config"]["subreddits"]
    EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
    EXCLUDED_USERS = set(data["config"]["excluded_users"])
    WHITELISTED_USERS = set(data["config"]["whitelisted_users"])
    MAX_WINNERS = data["config"]["max_winners"]
    MAX_REWARD = data["config"]["max_reward"]
    MIN_REWARD = data["config"].get("min_reward", 1000)
    last_processed_timestamp = data["last_processed_timestamp"]

try:
    reddit = login()
    logger.info("Logged in to Reddit successfully.")
except Exception:
    logger.exception("Failed to log in to Reddit.")
    sys.exit(1)

def safe_int(value, default=0):
    """
    Safely converts a value to an integer.

    Args:
        value: The value to convert.
        default (int, optional): The default value to use if conversion fails. Defaults to 0.

    Returns:
        int: The converted integer value, or the default if conversion fails.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid integer input: {value}. Using default {default}.")
        return default

def validate_parameters(num_winners, reward):
    """
    Validates and adjusts the parameters for the raffle to acceptable values.

    Args:
        num_winners (int): The number of winners requested.
        reward (int): The reward amount requested.

    Returns:
        tuple: The validated number of winners and reward amount.
    """
    num_winners = max(1, min(num_winners, MAX_WINNERS))
    if reward != 0:
        reward = max(MIN_REWARD, min(reward, MAX_REWARD))

    if num_winners < 1:
        logger.warning("num_winners less than 1; adjusted to 1.")
    elif num_winners > MAX_WINNERS:
        logger.warning(f"num_winners exceeded MAX_WINNERS; adjusted to {MAX_WINNERS}.")

    if reward < 0:
        logger.warning("Negative reward adjusted to 0.")
    elif reward > MAX_REWARD:
        logger.warning(f"Reward exceeded MAX_REWARD; adjusted to {MAX_REWARD}.")

    return num_winners, reward

def parse_command(command_text):
    """
    Parses the raffle command and extracts the parameters.

    Args:
        command_text (str): The text of the command to parse.

    Returns:
        tuple: The number of winners and reward, or (None, None) if the command is invalid.
    """
    match = re.match(TRIGGER, command_text.strip())
    if not match:
        return None, None  # Invalid command

    num_winners_str = match.group(1)
    reward_str = match.group(2)

    num_winners = safe_int(num_winners_str, default=1)
    reward = safe_int(reward_str, default=0)

    num_winners, reward = validate_parameters(num_winners, reward)

    return num_winners, reward

def send_reward_to_winners(winners, reward, raffle_id):
    """
    Sends a direct message to each winner with the reward amount asynchronously.

    Args:
        winners (list): A list of winners.
        reward (int): The reward amount to send.
        raffle_id (int): The ID of the raffle.
    """
    def send_rewards():
        for winner in winners:
            message_subject = f"Reward Raffle {raffle_id}"
            message_body = f"send {reward} u/{winner}"
            try:
                reddit.redditor("Canna_Tips").message(
                    subject=message_subject,
                    message=message_body
                )
                logger.info(f"Reward of {reward} sent to u/{winner} in raffle {raffle_id}.")
            except Exception:
                logger.exception(f"Failed to send reward to u/{winner}.")
            time.sleep(60)  # Wait 1 minute between each reward distribution

    threading.Thread(target=send_rewards, daemon=True).start()

def should_rate_limit(user):
    """
    Checks if the response to an invalid command from a user should be rate-limited.

    Args:
        user (str): The username to check.

    Returns:
        bool: True if the user should be rate-limited, False otherwise.
    """
    with rate_limit_lock:
        now = time.time()
        timestamps = invalid_command_timestamps.get(user, [])
        # Remove timestamps older than an hour
        timestamps = [t for t in timestamps if now - t < 3600]
        if len(timestamps) >= 3:
            return True
        timestamps.append(now)
        invalid_command_timestamps[user] = timestamps
        return False

def monitor_subreddit(subreddit_name):
    """
    Monitors a single subreddit for comments that trigger the raffle.

    Args:
        subreddit_name (str): The name of the subreddit to monitor.
    """
    subreddit = reddit.subreddit(subreddit_name)
    logger.info(f"Monitoring subreddit: {subreddit_name}")
    global last_processed_timestamp
    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            process_comment(comment, subreddit_name)
    except Exception:
        logger.exception(f"Error while monitoring subreddit {subreddit_name}.")

def process_comment(comment, subreddit_name):
    """
    Processes a comment to check if it contains a valid raffle command.

    Args:
        comment (praw.models.Comment): The comment to process.
        subreddit_name (str): The name of the subreddit in which the comment was posted.
    """
    if not is_new_comment(comment):
        return

    author_name = get_author_name(comment.author)

    num_winners, reward = parse_command(comment.body)
    if num_winners is None:
        handle_invalid_command(comment, author_name, subreddit_name)
        return

    handle_raffle(comment, num_winners, reward, subreddit_name)

def is_new_comment(comment):
    """
    Checks if the comment is new and has not been processed yet.

    Args:
        comment (praw.models.Comment): The comment to check.

    Returns:
        bool: True if the comment is new, False otherwise.
    """
    with data_lock:
        global last_processed_timestamp
        if comment.created_utc <= last_processed_timestamp:
            return False
        last_processed_timestamp = max(last_processed_timestamp, comment.created_utc)
        data["last_processed_timestamp"] = last_processed_timestamp
        save_data(data)
    return True

def get_author_name(author):
    """
    Retrieves the name of the author.

    Args:
        author (praw.models.Redditor or None): The author object.

    Returns:
        str: The name of the author, or "[deleted]" if the author is None.
    """
    return author.name if author else DELETED_USER

def handle_invalid_command(comment, author_name, subreddit_name):
    """
    Handles an invalid raffle command.

    Args:
        comment (praw.models.Comment): The comment containing the invalid command.
        author_name (str): The name of the comment author.
        subreddit_name (str): The name of the subreddit in which the command was posted.
    """
    if is_authorized_user(author_name, subreddit_name):
        if not should_rate_limit(author_name):
            reply_invalid_command(comment)
        else:
            logger.info(f"Rate limiting invalid command responses for u/{author_name}.")
    else:
        logger.warning(f"Invalid command format by unauthorized user u/{author_name}. No reply sent.")

def is_authorized_user(author_name, subreddit_name):
    """
    Checks if the user is authorized to use the bot.

    Args:
        author_name (str): The name of the user to check.
        subreddit_name (str): The subreddit in which the command was posted.

    Returns:
        bool: True if the user is authorized, False otherwise.
    """
    return is_moderator(reddit, author_name, subreddit_name) or author_name in WHITELISTED_USERS

def reply_invalid_command(comment):
    """
    Replies to a comment with an invalid command format message.

    Args:
        comment (praw.models.Comment): The comment to reply to.
    """
    try:
        comment.reply(
            "Invalid command format. Please use `!raffle w [number of winners] r [reward amount]`." + signature
        )
    except Exception:
        logger.exception("Failed to reply to invalid command.")
    logger.warning(f"Invalid command format by authorized user u/{comment.author.name}: {comment.body}")

def handle_raffle(trigger_comment, num_winners, reward, subreddit_name):
    """
    Handles the raffle process by selecting winners and notifying participants.

    Args:
        trigger_comment (praw.models.Comment): The comment that triggered the raffle.
        num_winners (int): The number of winners to select.
        reward (int): The reward amount for each winner.
        subreddit_name (str): The name of the subreddit where the raffle was triggered.
    """
    try:
        post = trigger_comment.submission
        post.comments.replace_more(limit=None)
        participants = {
            c.author.name for c in post.comments.list()
            if c.author
            and c.author.name not in EXCLUDED_BOTS
            and c.author.name != trigger_comment.author.name
            and c.author.name not in EXCLUDED_USERS
        }

        if len(participants) < num_winners:
            try:
                trigger_comment.reply(
                    f"Not enough participants to select {num_winners} winners." + signature
                )
            except Exception:
                logger.exception("Failed to reply about insufficient participants.")
            return

        winners = random.sample(participants, num_winners)
        winners_text = '\n'.join(f"- u/{winner}" for winner in winners)

        response_text = (
            f"**Raffle completed!**\n\n"
            f"**Winners:**\n{winners_text}\n\n"
            f"Thank you all for participating!\n\n"
            f"{signature}"
        )
        try:
            trigger_comment.reply(response_text)
        except Exception:
            logger.exception("Failed to reply with raffle results.")
        logger.info(f"Raffle completed in thread {post.id}. Winners: {winners}")

        with data_lock:
            data["config"]["raffle_count"] += 1
            save_data(data)

        if reward > 0:
            send_reward_to_winners(winners, reward, data["config"]["raffle_count"])

    except Exception:
        logger.exception("Error in handling raffle.")

def monitor_subreddits():
    """
    Starts a thread for each subreddit to monitor them concurrently.
    """
    logger.info("Starting subreddit monitoring...")
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SUBREDDITS)) as executor:
        futures = {executor.submit(monitor_subreddit, subreddit): subreddit for subreddit in SUBREDDITS}
        try:
            while True:
                time.sleep(0.1)
                print(f"Bot running... {next(spinner)}", end="\r")
                # Check for any exceptions in the futures
                done, _ = concurrent.futures.wait(
                    futures.keys(), timeout=0, return_when=concurrent.futures.FIRST_EXCEPTION
                )
                for future in done:
                    subreddit = futures[future]
                    try:
                        future.result()
                    except Exception:
                        logger.exception(f"Thread monitoring {subreddit} terminated unexpectedly.")
                        # Restart the thread
                        futures[executor.submit(monitor_subreddit, subreddit)] = subreddit
                        del futures[future]
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
        except Exception as e:
            logger.exception("Unexpected error in monitoring loop.")

if __name__ == "__main__":
    monitor_subreddits()
