import os
import re
import json
import requests
import logging
from bot import login, is_moderator

# Logging configuration
logging.basicConfig(
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

CONFIG_FILE = "bot_config.json"
TRIGGER = r'!canna-raffler\s*(\d*)'
RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")

def load_data():
    """Loads data from the JSON file, creating defaults if file is missing."""
    default_data = {
        "config": {
            "subreddits": ["MainSubreddit"],
            "max_winners": 5,
            "excluded_bots": ["AutoModerator", "timee_bot"],
            "excluded_users": [],
            "raffle_count": 0
        },
        "processed_posts": [],
        "last_processed_timestamp": 0
    }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    else:
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
MAX_WINNERS = data["config"]["max_winners"]

reddit = login()

def monitor_subreddits():
    """Monitors subreddits and handles raffles when trigger is detected."""
    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        logging.info(f"Monitoring subreddit: {subreddit_name}")
        print(f"Monitoring subreddit: {subreddit_name}")
        for comment in subreddit.stream.comments(skip_existing=True):
            if comment.created_utc <= data["last_processed_timestamp"]:
                continue
            
            if match := re.search(TRIGGER, comment.body):
                num_winners = int(match.group(1)) if match.group(1) else 1
                num_winners = min(num_winners, MAX_WINNERS)
                handle_raffle(comment, num_winners, subreddit_name)
                
            data["last_processed_timestamp"] = max(data["last_processed_timestamp"], comment.created_utc)
            save_data(data)

def get_random_numbers(n, min_val, max_val):
    """Fetches unique random numbers from Random.org, with fallback."""
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
    response = requests.post(url, json=params, headers=headers)
    if response.status_code == 200:
        return response.json().get("result", {}).get("random", {}).get("data", [])
    else:
        logging.error("Error in Random.org request. Using local random fallback.")
        import random
        return random.sample(range(min_val, max_val + 1), n)

def handle_raffle(trigger_comment, num_winners, subreddit_name):
    """Handles the raffle process, excluding post and trigger authors."""
    author_name = trigger_comment.author.name
    post_author_name = trigger_comment.submission.author.name
    post_id = trigger_comment.submission.id

    if post_id in PROCESSED_POSTS:
        logging.info(f"Post {post_id} already processed. Ignoring.")
        return

    if not is_moderator(reddit, author_name, subreddit_name):
        trigger_comment.reply("This bot is currently reserved for subreddit moderators.")
        logging.warning(f"User {author_name} attempted unauthorized bot usage.")
        print(f"User {author_name} attempted unauthorized bot usage.")
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

    # Detailed response with GIF link, winners tagged, and participants not tagged
    response_text = (
        f"**Raffle completed!**\n\n"
        f"**Qualified participants:**\n{participants_text}\n\n"
        f"**Winners:**\n{winners_text}\n\n"
        f"Thank you all for participating!"
    )
    trigger_comment.reply(response_text)
    logging.info(f"Raffle completed in thread {post_id}. Winners: {winners}")
    print(f"Raffle completed in thread {post_id}. Winners: {winners}")
    print(f"Starting subreddit monitoring...")

if __name__ == "__main__":
    logging.info("Starting subreddit monitoring...")
    print(f"Starting subreddit monitoring...")
    monitor_subreddits()
