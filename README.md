# Cannacoin Subreddit Raffle Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/language-Python-blue.svg)

Welcome to the **Cannacoin Subreddit Raffle Bot**! 🎉 This bot is designed to organize raffles and manage giveaways directly within designated subreddits. With a wide range of customizable settings, this bot simplifies rewarding community members with ease and transparency.

------

## Features

- **Multi-Subreddit Support**: Monitors multiple subreddits for raffle commands.
- **Configurable Prizes**: Customizable rewards based on ranking with flexible control over prize distribution.
- **Spam and Flood Control**: Automatically limits the frequency of raffle commands and applies user eligibility criteria.
- **User Notifications**: Directs important messages to designated moderators or administrators via DM.
- **Backup & Logs**: Automatic backups and rotating logs for reliability and stability.
- **Random.org API Integration**: For truly random winner selection (with a fallback to local random selection).

## Installation

1. **Clone the repository**:

   ```
   bashCopia codicegit clone https://github.com/username/cannacoin-raffle-bot.git
   cd cannacoin-raffle-bot
   ```

2. **Set up your environment variables**:

   - Create a `.env` file or export the variables in your environment:

   ```
   plaintextCopia codiceAPP_ID=your_app_id
   APP_SECRET=your_app_secret
   APP_REFRESH=your_refresh_token
   REDDIT_USERNAME=your_bot_username
   REDDIT_PASSWORD=your_bot_password
   RANDOM_ORG_API_KEY=your_random_org_key
   ```

3. **Install dependencies**:

   ```
   bash
   
   
   Copia codice
   pip install -r requirements.txt
   ```

4. **Configure the bot**: Modify `bot_config.json` for your subreddit settings, user permissions, and prize limits.

5. **Run the bot**:

   ```
   bash
   
   
   Copia codice
   python Cannacoin-Sub-Raffler.py
   ```

------

## Configuration

**bot_config.json** is where you customize the bot's settings. Here’s a quick overview of key parameters:

- `subreddits`: List of subreddits the bot should monitor.
- `max_winners`: Maximum number of winners per raffle.
- `max_reward` / `min_reward`: Limits for rewards distributed per raffle.
- `min_account_age_days` / `min_comment_karma`: Minimum requirements for users to participate.
- `excluded_bots`, `excluded_users`, `whitelisted_users`: Lists for filtering users and bots.
- `deusexmachina`: Administrator username for receiving notifications.

------

## Usage

To launch a raffle in a monitored subreddit, post a comment using the `!raffle` command with optional parameters for winners and rewards. The bot will manage everything from selecting winners to notifying participants.

**Basic Raffle Command:**

- `!raffle w 3 r 10000;5000;1000`: Start a raffle for 3 winners with prizes of 10000, 5000, and 1000 for each place, respectively.

For more detailed usage and behavior explanations, see the [User Guide](#user-guide) below.

------

## Backup and Logging

The bot creates a backup every 6 hours, with old backups automatically removed to keep storage manageable. Logs are saved in `bot.log` with a rotating file handler to prevent excessive log growth. These logs provide insight into the bot's activity and errors, aiding in smooth operation.

------

## License

This bot is available under the MIT License.

------

# User Guide

- [How to Start a Raffle](#how-to-start-a-raffle)
- [Command Parameters](#command-parameters)
- [Bot Behavior in Specific Situations](#bot-behavior-in-specific-situations)
- [Troubleshooting](#troubleshooting)

------

### How to Start a Raffle

To initiate a raffle, simply comment with the command `!raffle` followed by optional parameters to customize the raffle. Here's a quick overview:

#### Syntax:

```
plaintext


Copia codice
!raffle w <number_of_winners> r <reward1;reward2;reward3...>
```

#### Example:

- `!raffle w 3 r 10000;5000;1000`: Launch a raffle with 3 winners. The first winner receives 10000, the second 5000, and the third 1000.

#### Default Behavior:

- If no parameters are specified, the bot will default to 1 winner with no rewards.

------

### Command Parameters

| Parameter        | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| `w <number>`     | Defines the number of winners (default is 1).                |
| `r <reward;...>` | Specifies rewards per place, separated by `;`. Additional winners receive the last reward specified. |

**Note**: The bot enforces limits on the number of winners and reward amounts as specified in `bot_config.json`.

------

### Bot Behavior in Specific Situations

1. **Flood Control**:
   - Users can trigger a raffle every 10 minutes to prevent spam. Any excess commands are ignored, and the administrator receives a notification.
2. **Eligibility Check**:
   - The bot checks account age, karma, and other requirements before a user can participate. Ineligible participants are excluded automatically.
3. **Error and Feedback**:
   - Invalid commands or configurations prompt the bot to notify the designated administrator directly, ensuring smooth operations and troubleshooting.
4. **Multiple Subreddit Support**:
   - The bot can monitor multiple subreddits concurrently and will respond to valid raffle commands in each.

------

### Troubleshooting

If the bot stops or isn’t responding as expected:

1. **Check Logs**: Refer to `bot.log` for any errors or warnings.
2. **Verify Configuration**: Ensure `bot_config.json` is correctly set up, and environment variables are properly defined.
3. **Restart the Bot**: Stop the bot and relaunch it by running `python Cannacoin-Sub-Raffler.py`.

For further help, refer to the [GitHub Issues](https://github.com/username/cannacoin-raffle-bot/issues) page to report bugs or request assistance.
