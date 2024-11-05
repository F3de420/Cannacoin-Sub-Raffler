# Cannacoin-Sub-Raffler Bot

![Python Version](https://img.shields.io/badge/Python-3.x-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

This is a Reddit raffle bot developed for the **Stellar CANNACOIN** subreddit. It allows subreddit moderators to trigger a raffle in a post, automatically selecting random winners from eligible participants. The bot excludes spammer users and bots and only allows one raffle per post.

---

## Features

- Automatically monitoring specified subreddits for raffle triggers.
- Uses the [Random.org API](https://random.org) for drawing unique random numbers.
- Excludes specified users and bots from raffles.
- Notifies winner

---

## Prerequisites

- Python 3.x installed.
- A Reddit application and account for the bot.

---

## Installation

Clone the repository:
```bash
git clone https://github.com/YourUsername/Cannacoin-Sub-Raffler.git
cd Cannacoin-Sub-Raffler
```

Install dependencies:

```
pip install -r requirements.txt
```

------

## Setup and Configuration

1. **Create a Reddit Application:**

   - Go to [Reddit's App Preferences](https://www.reddit.com/prefs/apps).
   - Click on **Create App** or **Create Another App**.
   - Set **App Type** to **script**.
   - Fill out **name**, **redirect URI** (e.g., `http://localhost:8080`), and **description**.
   - Save your **Client ID** (under the app's name) and **Client Secret**.

2. **Obtain Refresh Token:**

   - Follow instructions from the [PRAW documentation](https://praw.readthedocs.io/) to obtain a refresh token.

3. **Set Environment Variables:** Add the following to your environment or use a `.env` file:

   ```
   export APP_ID="your_client_id"
   export APP_SECRET="your_client_secret"
   export APP_REFRESH="your_refresh_token"
   export REDDIT_USERNAME="your_bot_username"
   export REDDIT_PASSWORD="your_bot_password"
   export RANDOM_ORG_API_KEY="your_random_org_api_key"
   ```

4. **Configure `bot_config.json`:**

   Update `bot_config.json` with your subreddit, excluded users/bots, and other settings:

   ```
   {
       "config": {
           "subreddits": ["your_subreddit"],
           "max_winners": 10,
           "excluded_bots": ["AutoModerator", "timee_bot"],
           "excluded_users": ["spammer_user"],
           "raffle_count": 0
       },
       "processed_posts": [],
       "last_processed_timestamp": 0
   }
   ```

------

## Running the Bot

To start the bot manually:

```
python3 cannacoin-sub-raffler.py
```

------

## Code Overview

### `cannacoin-sub-raffler.py`

This is the main script responsible for monitoring comments, handling the raffle, and replying with the results.

#### Key Functions:

- **load_data**: Loads configuration and processed posts from `bot_config.json`. Logs a warning if using default data.
- **monitor_subreddits**: Monitors subreddit comments and triggers the raffle function.
- **get_random_numbers**: Fetches random numbers from Random.org, with a local fallback in case of error.
- **handle_raffle**: Handles the raffle logic, excluding certain users and handling single-raffle-per-post logic.

### `bot.py`

Contains the functions for logging into Reddit via PRAW and verifying moderator status.

------

## Example Usage

To trigger a raffle, a moderator can comment `!<TRIGGER>` in a post on the configured subreddit. The bot will:

- Check if a raffle has already been held in the post.
- Select random winners from the eligible participants.

------

## Requirements

```
praw
requests
```

------

## License

This project is licensed under the MIT License.
