# Cannacoin Subreddit Raffle Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/language-Python-blue.svg)

A Reddit bot for managing raffles in specified subreddits, designed to help moderators organize giveaways effectively by selecting winners based on custom criteria.

## Features

- **Automated Raffles**: Monitors specified subreddits and detects raffle commands (`!raffle`) in comments.
- **Customizable Rules**: Configurable settings for maximum winners, prize limits, account age, and comment karma requirements.
- **Anti-Flood Control**: Limits raffle triggers to prevent spam and unauthorized access.
- **Manual Prize Distribution**: Posts results and prompts winners to reply for reward arrangement.
- **Data Logging and Backup**: Rotating logs with periodic configuration backups and keep-alive messages for reliable monitoring.

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/username/Cannacoin-Sub-Raffler.git
   cd Cannacoin-Sub-Raffler

1. **Install Requirements**

   - Install dependencies for the Reddit API using `praw`.

   ```
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**

   - Set up environment variables for Reddit API access in your environment:

     ```
     export APP_ID=your_app_id
     export APP_SECRET=your_app_secret
     export APP_REFRESH=your_refresh_token
     export REDDIT_USERNAME=your_bot_username
     export REDDIT_PASSWORD=your_bot_password
     export RANDOM_ORG_API_KEY=your_random_org_api_key
     ```

3. **Edit Configuration (bot_config.json)**

   - Modify 

     ```
     bot_config.json
     ```

      to specify:

     - **Subreddits** to monitor
     - **User and bot exclusions**
     - **Raffle limits** like max winners and reward range

4. **Run the Bot**

   ```
   python Cannacoin-Sub-Raffler.py
   ```

## Command Usage

- Start a Raffle

  : Users with the required permissions can start a raffle by commenting:

  ```
  !raffle w <num_winners> r <reward_amount>
  ```

  - `<num_winners>` (optional): Number of winners, limited by `max_winners`.
  - `<reward_amount>` (optional): Reward per winner, must be within `min_reward` and `max_reward`.

### Examples of Commands

- `!raffle`
  - Starts a raffle with 1 winner and no reward.
- `!raffle w 3`
  - Starts a raffle with 3 winners and no reward. The `max_winners` setting still applies.
- `!raffle r 500`
  - Starts a raffle with 1 winner, each receiving a reward of 500 (within the `min_reward` and `max_reward` limits).
- `!raffle w 2 r 1000`
  - Starts a raffle with 2 winners, each receiving a reward of 1000. Both `max_winners` and reward limits apply.

## Configuration File (`bot_config.json`)

The `bot_config.json` file contains settings for:

- Subreddit list (`subreddits`)
- User and bot exclusions (`excluded_bots`, `excluded_users`)
- Winner count and prize limits (`max_winners`, `max_reward`, `min_reward`)
- Minimum account age and karma for eligibility (`min_account_age_days`, `min_comment_karma`)

## Logging and Backup

- **Logging**: Tracks bot actions and raffle activities with rotating logs (`bot.log`).
- **Backup**: Configuration file is backed up every 6 hours with a maximum of 10 backups.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
