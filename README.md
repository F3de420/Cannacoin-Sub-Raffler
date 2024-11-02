# Cannacoin-Sub-Raffler

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![GitHub](https://img.shields.io/badge/License-MIT-brightgreen)

## Overview

# Canna_Raffler_Bot

## Description

This bot randomly selects winners in a specified subreddit when triggered by the `!canna-raffler` command. The bot is restricted to moderators and uses the Random.org API to generate true randomness based on atmospheric noise.

## Features

- Monitors comments in configured subreddits.
- Recognizes the `!canna-raffler <num>` command.
- Supports a configurable number of winners.
- Excludes specific users and bots from selection.
- Supports data persistence between restarts.

## Configuration

### Prerequisites

1. **Python 3.8+**
2. **Environment Variables**: Set up the following environment variables:

   - `APP_ID`: Reddit app ID
   - `APP_SECRET`: Reddit app secret
   - `APP_REFRESH`: Reddit app refresh token
   - `REDDIT_USERNAME`: Reddit bot username
   - `REDDIT_PASSWORD`: Reddit bot password
   - `RANDOM_ORG_API_KEY`: Random.org API key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/canna_raffler_bot.git
   cd canna_raffler_bot
2. Install required packages:
   ```bash
   pip install -r requirements.txt
3. Set up your Reddit application:

   -  Go to Reddit Apps.
   - Create a new application.
   - Take note of your client_id and client_secret.
   - Make sure to set the redirect URI to http://www.example.com/unused/redirect/uri.   

5. Set up environment variables as described.


### Running the Bot

Start the bot with the following command:
```bash
python raffler.py
