import os
import re
import json
import requests
from bot import login, is_moderator

# File and trigger configuration
CONFIG_FILE = "bot_data.json"
TRIGGER = r'!canna-raffler\s*(\d*)'
RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")  # API key as an environment variable

# Load persistent data
def load_data():
    """Loads persistent data from JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"config": {"subreddits": ["MainSubreddit"], "max_winners": 5, 
                       "excluded_bots": ["AutoModerator", "timee_bot"], "excluded_users": [], "raffle_count": 0},
            "processed_posts": [], "last_processed_timestamp": 0}

# Save persistent data
def save_data(data):
    """Saves persistent data to JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Initialize loaded data
data = load_data()
PROCESSED_POSTS = set(data["processed_posts"])
SUBREDDITS = data["config"]["subreddits"]
EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
EXCLUDED_USERS = set(data["config"]["excluded_users"])
MAX_WINNERS = data["config"]["max_winners"]

# Initialize Reddit
reddit = login()

def monitor_subreddits():
    """Monitors the subreddits and handles raffle when the trigger is detected."""
    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
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
    """Fetches `n` unique random numbers from Random.org between min_val and max_val."""
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
        result = response.json().get("result", {}).get("random", {}).get("data", [])
        return result
    else:
        raise Exception("Error in Random.org request")

def handle_raffle(trigger_comment, num_winners, subreddit_name):
    """Handles the raffle process."""
    author_name = trigger_comment.author.name
    post_id = trigger_comment.submission.id

    if post_id in PROCESSED_POSTS:
        print(f"The bot has already processed post {post_id}. Operation ignored.")
        return

    if not is_moderator(reddit, author_name, subreddit_name):
        trigger_comment.reply("This bot is currently reserved for subreddit moderators.")
        print(f"User {author_name} attempted to use the bot without permissions.")
        return

    PROCESSED_POSTS.add(post_id)
    data["processed_posts"] = list(PROCESSED_POSTS)
    save_data(data)

    post = trigger_comment.submission
    post.comments.replace_more(limit=None)
    all_comments = post.comments.list()

    participants = set()
    for comment in all_comments:
        if comment.author and comment.author.name not in EXCLUDED_BOTS \
                and comment.author.name != author_name \
                and comment.author.name not in EXCLUDED_USERS:
            participants.add(comment.author.name)

    participants_list = list(participants)
    if len(participants_list) < num_winners:
        trigger_comment.reply(f"There are not enough participants to select {num_winners} winners.")
        return

    # Use Random.org to draw random indices of winners
    try:
        winner_indices = get_random_numbers(num_winners, 0, len(participants_list) - 1)
        winners = [participants_list[i] for i in winner_indices]
    except Exception as e:
        print("Error in Random.org draw:", e)
        trigger_comment.reply("There was an error in selecting the winners.")
        return

    winners_text = '\n'.join(f"- {winner}" for winner in winners)
    data["config"]["raffle_count"] += 1
    save_data(data)

    response_text = f"🎉 **Raffle completed!**\n\nHere are the winners:\n\n{winners_text}\n\nThanks to everyone for participating!"
    trigger_comment.reply(response_text)
    print(f"Raffle completed in thread {post.id}. Winners: {winners}")

if __name__ == "__main__":
    print("Starting subreddit monitoring...")
    monitor_subreddits()
