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

# Lock for synchronizing access to shared data
data_lock = threading.Lock()
# Lock for rate limiting invalid command responses
rate_limit_lock = threading.Lock()
invalid_command_timestamps = {}

def load_data():
    """Loads data from the JSON file, creating defaults if file is missing."""
    default_data = {
        "config": {
            "subreddits": ["MainSubreddit"],
            "max_winners": 5,
            "max_reward": 100,
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
    """Saves data to JSON file with thread-safe access."""
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
    last_processed_timestamp = data["last_processed_timestamp"]

try:
    reddit = login()
    logger.info("Logged in to Reddit successfully.")
except Exception as e:
    logger.exception("Failed to log in to Reddit.")
    sys.exit(1)

def safe_int(value, default=0):
    """Converts a value to int safely."""
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid integer input: {value}. Using default {default}.")
        return default

def validate_parameters(num_winners, reward):
    """Validates and adjusts the parameters to acceptable values."""
    if num_winners < 1:
        logger.warning("num_winners less than 1; adjusted to 1.")
        num_winners = 1
    elif num_winners > MAX_WINNERS:
        logger.warning(f"num_winners exceeded MAX_WINNERS; adjusted to {MAX_WINNERS}.")
        num_winners = MAX_WINNERS

    if reward < 0:
        logger.warning("Negative reward adjusted to 0.")
        reward = 0
    elif reward > MAX_REWARD:
        logger.warning(f"Reward exceeded MAX_REWARD; adjusted to {MAX_REWARD}.")
        reward = MAX_REWARD

    return num_winners, reward

def parse_command(command_text):
    """Parses the command and extracts parameters."""
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
    """Sends a DM to Canna_Tips for each winner with the reward amount asynchronously."""
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
    """Checks if we should rate limit responses to invalid commands from this user."""
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
    """Monitors a single subreddit for comments that trigger the raffle."""
    subreddit = reddit.subreddit(subreddit_name)
    logger.info(f"Monitoring subreddit: {subreddit_name}")
    global last_processed_timestamp
    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            with data_lock:
                if comment.created_utc <= last_processed_timestamp:
                    continue
                last_processed_timestamp = max(last_processed_timestamp, comment.created_utc)
                data["last_processed_timestamp"] = last_processed_timestamp
                save_data(data)

            author_name = comment.author.name if comment.author else "[deleted]"

            # Check for trigger command in comment with input validation
            num_winners, reward = parse_command(comment.body)
            if num_winners is None:
                # Invalid command format
                if is_moderator(reddit, author_name, subreddit_name) or author_name in WHITELISTED_USERS:
                    if not should_rate_limit(author_name):
                        try:
                            comment.reply(
                                "Invalid command format. Please use `!raffle w [number of winners] r [reward amount]`." + signature
                            )
                        except Exception as e:
                            logger.exception("Failed to reply to invalid command.")
                        logger.warning(f"Invalid command format by authorized user u/{author_name}: {comment.body}")
                    else:
                        logger.info(f"Rate limiting invalid command responses for u/{author_name}.")
                else:
                    logger.warning(f"Invalid command format by unauthorized user u/{author_name}. No reply sent.")
                continue

            handle_raffle(comment, num_winners, reward, subreddit_name)
    except Exception as e:
        logger.exception(f"Error while monitoring subreddit {subreddit_name}.")

def monitor_subreddits():
    """Starts a thread for each subreddit to monitor them concurrently."""
    logger.info("Starting subreddit monitoring...")
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SUBREDDITS)) as executor:
        futures = {executor.submit(monitor_subreddit, subreddit): subreddit for subreddit in SUBREDDITS}
        try:
            while True:
                time.sleep(0.1)
                print(f"Bot running... {next(spinner)}", end="\r")
                # Check for any exceptions in the futures
                done, not_done = concurrent.futures.wait(
                    futures.keys(), timeout=0, return_when=concurrent.futures.FIRST_EXCEPTION
                )
                for future in done:
                    subreddit = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.exception(f"Thread monitoring {subreddit} terminated unexpectedly.")
                        # Restart the thread
                        futures[executor.submit(monitor_subreddit, subreddit)] = subreddit
                        del futures[future]
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
        except Exception as e:
            logger.exception("Unexpected error in monitoring loop.")

def get_random_numbers(n, min_val, max_val):
    """Fetches unique random numbers from Random.org, with a fallback to local random."""
    if RANDOM_ORG_API_KEY:
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
            "id": random.randint(1, 100000)
        }
        try:
            response = requests.post(url, json=params, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get("result", {}).get("random", {}).get("data", [])
        except Exception as e:
            logger.exception("Error in Random.org request. Using local random fallback.")

    # Local random fallback
    return random.sample(range(min_val, max_val + 1), n)

def handle_raffle(trigger_comment, num_winners, reward, subreddit_name):
    """Handles the raffle process, excluding post and trigger authors."""
    try:
        author_name = trigger_comment.author.name if trigger_comment.author else "[deleted]"
        post_author = trigger_comment.submission.author
        post_author_name = post_author.name if post_author else "[deleted]"
        post_id = trigger_comment.submission.id

        with data_lock:
            if post_id in PROCESSED_POSTS:
                logger.info(f"Post {post_id} already processed. Ignoring.")
                try:
                    trigger_comment.reply("A raffle has already been completed in this post." + signature)
                except Exception as e:
                    logger.exception("Failed to reply about already processed post.")
                return

            if not (is_moderator(reddit, author_name, subreddit_name) or author_name in WHITELISTED_USERS):
                try:
                    trigger_comment.reply(
                        "This bot is currently reserved for subreddit moderators and approved users." + signature
                    )
                except Exception as e:
                    logger.exception("Failed to reply about unauthorized usage.")
                logger.warning(f"Unauthorized bot usage attempt by u/{author_name}.")
                return

            PROCESSED_POSTS.add(post_id)
            data["processed_posts"] = list(PROCESSED_POSTS)
            save_data(data)

        post = trigger_comment.submission
        post.comments.replace_more(limit=None)
        participants = {
            c.author.name for c in post.comments.list()
            if c.author
            and c.author.name not in EXCLUDED_BOTS
            and c.author.name != author_name
            and c.author.name != post_author_name
            and c.author.name not in EXCLUDED_USERS
        }

        if len(participants) < num_winners:
            try:
                trigger_comment.reply(
                    f"Not enough participants to select {num_winners} winners." + signature
                )
            except Exception as e:
                logger.exception("Failed to reply about insufficient participants.")
            logger.info("Not enough participants for the raffle.")
            return

        participants_list = list(participants)
        winner_indices = get_random_numbers(num_winners, 0, len(participants_list) - 1)
        winners = [participants_list[i] for i in winner_indices]
        winners_text = '\n'.join(f"- u/{winner}" for winner in winners)
        participants_text = '\n'.join(f"- u/{participant}" for participant in participants_list)

        with data_lock:
            data["config"]["raffle_count"] += 1
            raffle_id = data["config"]["raffle_count"]
            save_data(data)

        reward_text = f" with a reward of {reward}" if reward > 0 else ""
        gradual_reward_notice = (
            "\n\nNote: Rewards will be distributed gradually. "
            "Please don't worry if you don't receive the reward immediately, as they are sent one minute apart."
        ) if reward > 0 else ""

        response_text = (
            f"**Raffle completed!**\n\n"
            f"**Qualified participants:**\n{participants_text}\n\n"
            f"**Winners:**\n{winners_text}{reward_text}\n\n"
            f"Thank you all for participating!{gradual_reward_notice}\n\n"
            f"{signature}"
        )
        try:
            trigger_comment.reply(response_text)
        except Exception as e:
            logger.exception("Failed to reply with raffle results.")
        logger.info(
            f"Raffle {raffle_id} completed in thread {post_id}. "
            f"Winners: {winners} with reward: {reward}"
        )

        if reward > 0:
            send_reward_to_winners(winners, reward, raffle_id)

    except Exception as e:
        logger.exception("Error in handling raffle.")

if __name__ == "__main__":
    logger.info("Bot is starting...")
    try:
        monitor_subreddits()
    except Exception as e:
        logger.exception("Critical error. Bot is shutting down.")
