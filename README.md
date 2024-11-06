# Cannacoin-Sub-Raffler Bot

![Python Version](https://img.shields.io/badge/Python-3.x-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

### Overview

The **Cannacoin-Sub-Raffler** bot developed for the **[Stellar CANNACOIN subreddit](https://www.reddit.com/r/StellarCannaCoin/)** is a specialized Reddit bot developed to facilitate and manage raffle events within selected subreddits. By monitoring comments and processing user-triggered commands, this bot provides an automated solution for drawing random winners in a fair, efficient, and customizable way.

### Key Features

- **Dynamic Monitoring**: Concurrently monitors multiple subreddits, tracking specific trigger commands to initiate raffles.
- **User Permissions**: Only authorized users (subreddit moderators or whitelisted users) can trigger a raffle, providing control over the bot's operation.
- **Automated Winner Selection**: Leverages the [Random.org API](https://random.org) for unbiased winner selection, with a local fallback if the API is unavailable.
- **Configurable Settings**: Easily customizable through a configuration file (`bot_config.json`) that allows for adjustments to subreddits, excluded users/bots, and other settings.
- **Dynamic Reloading**: Automatically detects and applies changes to the configuration file without restarting, providing seamless updates to monitored subreddits or user permissions.

### Repository Structure

```
bashCopia codice.
├── Cannanoin-Sub-Raffler.py      # Main script handling subreddit monitoring and raffle processing.
├── bot.py                        # Helper script for logging into Reddit and checking user permissions.
├── bot_config.json               # Configuration file defining subreddits, max winners, and user restrictions.
└── README.md                     # Project documentation.
```

### Setup and Configuration

#### Prerequisites

1. **Python 3.8+**: Ensure Python is installed on your system.
2. **Reddit Account**: Register a Reddit application to obtain API credentials for bot authentication.
3. **Random.org API Key**: Generate an API key on [Random.org](https://random.org) if random number generation via their service is desired.

#### Installation

1. Clone the repository:

   ```
   bashCopia codicegit clone https://github.com/YourUsername/Cannacoin-Sub-Raffler.git
   cd Cannacoin-Sub-Raffler
   ```

2. Install required packages:

   ```
   bash
   
   
   Copia codice
   pip install praw requests
   ```

#### Environment Variables

Create a `.env` file or configure your environment with the following variables:

- **`APP_ID`**: Reddit API client ID.
- **`APP_SECRET`**: Reddit API client secret.
- **`APP_REFRESH`**: Reddit refresh token.
- **`REDDIT_USERNAME`**: Reddit account username.
- **`REDDIT_PASSWORD`**: Reddit account password.
- **`RANDOM_ORG_API_KEY`**: (Optional) API key for Random.org.

#### Configuration File (`bot_config.json`)

The `bot_config.json` file controls most aspects of the bot’s behavior:

- **`subreddits`**: List of subreddits to monitor for raffles.
- **`max_winners`**: Maximum number of winners for any raffle.
- **`excluded_bots`**: Bots to exclude from the raffle (e.g., `AutoModerator`).
- **`excluded_users`**: Specific users to exclude from the raffle.
- **`whitelisted_users`**: Users authorized to trigger raffles.
- **`raffle_count`**: Tracks the total number of raffles conducted.

> **Note**: This file dynamically updates while the bot is running, meaning changes will be detected and applied without needing to restart the bot.

### Usage

1. **Start the Bot**:

   ```
   bash
   
   
   Copia codice
   python Cannanoin-Sub-Raffler.py
   ```

   The bot will log into Reddit, start monitoring the specified subreddits, and log all activity to `bot.log`.

2. **Triggering a Raffle**:

   - Authorized users can initiate a raffle by posting a comment with the `!raffle` command in a monitored subreddit. The command accepts an optional number to specify the desired number of winners.
   - Example usage:
     - `!raffle 3` (selects up to 3 winners)
     - `!raffle` (selects 1 winner by default)

3. **Raffle Response**:

   - Once triggered, the bot gathers eligible participants from the post, excluding any defined in `excluded_users` or `excluded_bots`.
   - Winners are selected randomly, and the bot replies with the list of winners, thanking participants.

### Logging and Monitoring

- **Logging**: Activity and errors are logged to `bot.log`, allowing for easy tracking of bot actions and any issues encountered.
- **Configuration Reloading**: The bot checks for changes to `bot_config.json` every 10 seconds, applying any updates to monitored subreddits, whitelisted users, or excluded users in real time.

------

**Disclaimer**: This bot is provided as-is, without warranty of any kind. Use at your own risk and comply with Reddit’s Terms of Service and API Terms.

------

License

This project is licensed under the MIT License

------

Happy Raffle Hosting! 🎉

