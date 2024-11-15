# Cannacoin Subreddit Raffle Bot

A Reddit bot designed to manage and automate raffles in Cannacoin-related subreddits. The bot listens for specific commands in subreddit comments and conducts raffles by selecting winners, calculating rewards, and posting the results. It integrates with Random.org for randomness and Pastebin for sharing participant lists.

## Features

- Monitors multiple subreddits for raffle triggers.
- Supports custom number of winners and rewards per raffle.
- Ensures participants meet minimum account age and karma requirements.
- Excludes specified bots and users from participating.
- Uses Random.org API for unbiased winner selection.
- Uploads participant lists to Pastebin and shares the raw link.
- Logs all activities and errors to a rotating log file.

## Requirements

- Python 3.6 or higher
- Reddit account with API access
- Pastebin account with API access
- Random.org API key

## Dependencies

Install the required Python packages using `pip`:

```
pip install praw requests
```

## Installation

1. **Clone the Repository**

   ```
   git clone https://github.com/yourusername/cannacoin-raffle-bot.git
   cd cannacoin-raffle-bot
   ```

2. **Set Up Environment Variables**

   The bot uses environment variables for sensitive information. Set the following variables in your environment:

   - `APP_ID`: Reddit application client ID
   - `APP_SECRET`: Reddit application secret
   - `APP_REFRESH`: Reddit application refresh token
   - `REDDIT_USERNAME`: Reddit account username
   - `REDDIT_PASSWORD`: Reddit account password
   - `PASTEBIN_API_KEY`: Pastebin developer API key
   - `PASTEBIN_USERNAME`: Pastebin account username
   - `PASTEBIN_PASSWORD`: Pastebin account password
   - `RANDOM_ORG_API_KEY`: Random.org API key

   Example using `export` (Linux/macOS):

   ```
   export APP_ID='your_app_id'
   export APP_SECRET='your_app_secret'
   export APP_REFRESH='your_refresh_token'
   export REDDIT_USERNAME='your_reddit_username'
   export REDDIT_PASSWORD='your_reddit_password'
   export PASTEBIN_API_KEY='your_pastebin_api_key'
   export PASTEBIN_USERNAME='your_pastebin_username'
   export PASTEBIN_PASSWORD='your_pastebin_password'
   export RANDOM_ORG_API_KEY='your_random_org_api_key'
   ```

   On Windows, use `set` instead of `export`.

3. **Configure the Bot**

   Edit a `bot_config.json` file in the project directory-

   Adjust the configuration parameters according to your needs:

   - **subreddits**: List of subreddits to monitor.
   - **max_winners**: Maximum number of winners allowed per raffle.
   - **max_reward**: Maximum reward amount allowed.
   - **min_reward**: Minimum reward amount allowed.
   - **min_account_age_days**: Minimum account age in days required to participate.
   - **min_comment_karma**: Minimum comment karma required to participate.
   - **excluded_bots**: List of bot usernames to exclude from raffles.
   - **excluded_users**: List of user usernames to exclude from raffles.
   - **whitelisted_users**: List of users exempt from certain restrictions.
   - **deusexmachina**: Admin username for special permissions.

## Usage

Run the bot using Python:

```
python3 Cannacoin-Sub-Raffler.py
```

The bot will start monitoring the specified subreddits and display a spinner animation in the console to indicate that it's running.

### Raffle Trigger Syntax

To initiate a raffle, a user (usually a moderator or whitelisted user) comments using the following command:

```
!raffle4canna w [number_of_winners] r [reward1;reward2;...]
```

- **w [number_of_winners]**: (Optional) Specifies the number of winners. Defaults to 1 if omitted.
- **r [reward1;reward2;...]**: (Optional) Specifies the rewards for each winner, separated by semicolons.

**Examples:**

- `!raffle4canna`: Starts a raffle with 1 winner and no rewards.
- `!raffle4canna w 3`: Starts a raffle with 3 winners and no rewards.
- `!raffle4canna w 2 r 100;50`: Starts a raffle with 2 winners. The first winner gets 100 CANNACOIN, the second gets 50 CANNACOIN.

### Bot Response

After processing a raffle, the bot will reply with a message like:

```
**Raffle Completed!**

**Total Participants:** 15
[Full List of Eligible Participants](https://pastebin.com/raw/abc123)

**Total Reward Pool:** 150 CANNACOIN

**Winners:**
1. u/winner1 - 100 CANNACOIN
2. u/winner2 - 50 CANNACOIN

---

Thank you all for participating!

**Note:** All prizes will be distributed manually. Winners, please reply to this comment. Thank you for participating!

---

[Cannacoin Raffler](https://github.com/yourusername/cannacoin-raffle-bot) | [r/StellarCannaCoin](https://www.reddit.com/r/StellarCannaCoin/) | [r/StellarShroomz](https://www.reddit.com/r/StellarShroomz) | [StashApp](https://stashapp.cloud/) | [Cannacoin Discord](https://discord.gg/Xrpxm34QgW) | [Shroomz Discord](https://discord.gg/PXkKFKwZVA)
```

## Logs

All activities and errors are logged to `bot.log` in the project directory. The log file uses a rotating handler to manage file size.

## License

This project is licensed under the MIT License.

## Acknowledgments

- [PRAW](https://praw.readthedocs.io/): The Python Reddit API Wrapper.
- Requests: For handling HTTP requests.
- Random.org: For generating true random numbers.
- [Pastebin](https://pastebin.com/api): For sharing participant lists.

## Disclaimer

This bot is provided as-is without any warranties. Use it responsibly and adhere to Reddit's API terms and conditions.

------

*Happy raffling!*
