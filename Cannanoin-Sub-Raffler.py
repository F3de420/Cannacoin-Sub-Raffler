import os
import re
import json
import requests
import logging
from bot import login, is_moderator
import concurrent.futures
import time
import itertools

# Logging configuration
logging.basicConfig(
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

CONFIG_FILE = "bot_config.json"
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

def load_data():
    """Loads data from the JSON file, creating defaults if file is missing."""
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
    """Saves data to JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
PROCESSED_POSTS = set(data["processed_posts"])
SUBREDDITS = data["config"]["subreddits"]
EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
EXCLUDED_USERS = set(data["config"]["excluded_users"])
WHITELISTED_USERS = set(data["config"]["whitelisted_users"])
MAX_WINNERS = data["config"]["max_winners"]
last_processed_timestamp = data["last_processed_timestamp"]

try:
    reddit = login()
except Exception as e:
    logging.error(f"Failed to log in to Reddit: {e}")
    exit(1)

def send_reward_to_winners(winners, reward, raffle_id):
    """Sends a DM to Canna_Tips for each winner with the reward amount."""
    for winner in winners:
        message_subject = f"Reward Raffle {raffle_id}"
        message_body = f"send {reward} u/{winner}"
        try:
            reddit.redditor("Canna_Tips").message(
                subject=message_subject,
                message=message_body
            )
            logging.info(f"Reward of {reward} sent to u/{winner} in raffle {raffle_id}.")
        except Exception as e:
            logging.error(f"Failed to send reward to u/{winner}: {e}")
        time.sleep(60)  # Wait 1 minute between each reward distribution

def monitor_subreddit(subreddit_name):
    """Monitors a single subreddit for comments that trigger the raffle."""
    subreddit = reddit.subreddit(subreddit_name)
    logging.info(f"Monitoring subreddit: {subreddit_name}")
    global last_processed_timestamp
    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            if comment.created_utc <= last_processed_timestamp:
                continue
            
            # Check for trigger command in comment with optional `w` and `r` parameters
            if match := re.search(TRIGGER, comment.body):
                num_winners = int(match.group(1)) if match.group(1) else 1
                reward = int(match.group(2)) if match.group(2) else 0
                num_winners = min(num_winners, MAX_WINNERS)
                
                handle_raffle(comment, num_winners, reward, subreddit_name)
                
            last_processed_timestamp = max(last_processed_timestamp, comment.created_utc)
            data["last_processed_timestamp"] = last_processed_timestamp
            save_data(data)
    except Exception as e:
        logging.error(f"Error while monitoring subreddit {subreddit_name}: {e}")

def monitor_subreddits():
    """Starts a thread for each subreddit to monitor them concurrently."""
    logging.info("Starting subreddit monitoring...")
    spinner = itertools.cycle(['|', '/', '-', '\\'])

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while True:
            try:
                executor.map(monitor_subreddit, SUBREDDITS)
                time.sleep(1)
                print(f"Bot running... {next(spinner)}", end="\r")
                # Periodically save processed posts to ensure consistency
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

    if post_id in PROCESSED_POSTS:
        logging.info(f"Post {post_id} already processed. Ignoring.")
        trigger_comment.reply("A raffle has already been completed in this post." + signature)
        return

    if not (is_moderator(reddit, author_name, subreddit_name) or author_name in WHITELISTED_USERS):
        trigger_comment.reply("This bot is currently reserved for subreddit moderators and approved users." + signature)
        logging.warning(f"User {author_name} attempted unauthorized bot usage.")
        return

    PROCESSED_POSTS.add(post_id)
    data["processed_posts"] = list(PROCESSED_POSTS)
    save_data(data)

    post = trigger_comment.submission
    post.comments.replace_more(limit=None)
    participants = {
        c.author.name for c in post.comments.list()
        if c.author and c.author.name not in EXCLUDED_BOTS
        and c.author.name != author_name
        and c.author.name != post_author_name
        and c.author.name not in EXCLUDED_USERS
    }

    if len(participants) < num_winners:
        trigger_comment.reply(f"Not enough participants to select {num_winners} winners." + signature)
        logging.info("Not enough participants for the raffle.")
        return

    winner_indices = get_random_numbers(num_winners, 0, len(participants) - 1)
    participants_list = list(participants)
    winners = [participants_list[i] for i in winner_indices]
    winners_text = '\n'.join(f"- u/{winner}" for winner in winners)
    participants_text = '\n'.join(f"- {participant}" for participant in participants_list)

    data["config"]["raffle_count"] += 1
    raffle_id = data["config"]["raffle_count"]
    save_data(data)

    # Including the reward in the response if specified
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
    trigger_comment.reply(response_text)
    logging.info(f"Raffle completed in thread {post_id}. Winners: {winners} with reward: {reward}")

    # Send reward to winners via DM to Canna_Tips if reward is specified
    if reward > 0:
        send_reward_to_winners(winners, reward, raffle_id)

if __name__ == "__main__":
    logging.info("Starting subreddit monitoring...")
    monitor_subreddits()
