import os
import praw

# Configuration using environment variables
USERAGENT = 'Bot for raffle management on subreddit'
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
APP_REFRESH = os.getenv("APP_REFRESH")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

def login():
    """Logs into Reddit using refresh token authentication."""
    return praw.Reddit(
        user_agent=USERAGENT,
        client_id=APP_ID,
        client_secret=APP_SECRET,
        refresh_token=APP_REFRESH,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD
    )

def is_moderator(reddit_instance, username, subreddit_name):
    """Checks if the user is a moderator of the specified subreddit."""
    subreddit = reddit_instance.subreddit(subreddit_name)
    moderators = subreddit.moderator()
    return username in [mod.name for mod in moderators]