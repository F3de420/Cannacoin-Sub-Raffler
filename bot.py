import os
import praw

USERAGENT = 'Bot for managing raffle on subreddits'
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
APP_REFRESH = os.getenv("APP_REFRESH")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

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
