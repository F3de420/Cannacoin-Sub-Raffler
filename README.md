# Cannacoin Subreddit Raffle Bot

![Python Version](https://img.shields.io/badge/Python-3.x-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

A Reddit bot designed to manage raffles on Cannacoin-related subreddits. The bot monitors specified subreddits for raffle commands issued by authorized users, selects winners based on predefined criteria, announces the results, and distributes rewards in Cannacoin.

## Features

- **Automated Raffle Management**: Monitors comments in specified subreddits for raffle commands.
- **Participant Validation**: Ensures participants meet minimum account age and comment karma requirements.
- **Random Winner Selection**: Randomly selects winners from eligible participants.
- **Reward Distribution**: Sends Cannacoin rewards to winners via direct messages.
- **Customizable Settings**: Configure various parameters like maximum winners, reward amounts, and participation requirements.
- **Logging**: Detailed logging with log rotation for monitoring and debugging.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Usage](#usage)
- [Examples of Raffle Commands](#examples-of-raffle-commands)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- **Python 3.6 or higher**
- **Reddit Account**: With necessary permissions to read comments and send messages.
- **Reddit App Credentials**: Obtain client ID, client secret, and set up a refresh token.
- **Cannacoin Wallet**: For distributing rewards (optional if rewards are managed externally).

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/Cannacoin-Sub-Raffler.git
   cd Cannacoin-Sub-Raffler
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   *If a `requirements.txt` file is not provided, install the necessary packages manually:*

   ```bash
   pip install praw
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the project directory or set the following environment variables:

   ```bash
   APP_ID=your_reddit_app_id
   APP_SECRET=your_reddit_app_secret
   APP_REFRESH=your_reddit_refresh_token
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   ```

   *Replace the placeholders with your actual Reddit app credentials and account information.*

## Configuration

The bot uses a JSON configuration file named `bot_config.json`. This file contains settings for subreddits to monitor, user permissions, participation requirements, and more.

### **bot_config.json**

```json
{
    "config": {
        "subreddits": [
            "subreddit_1",
            "Subreddit_2"
        ],
        "max_winners": 5,
        "max_reward": 10000,
        "min_reward": 1000,
        "min_account_age_days": 7,
        "min_comment_karma": 100,
        "excluded_bots": [
            "bot_1",
            "bot_2"
        ],
        "excluded_users": [],
        "whitelisted_users": [
            "your_reddit_username"
        ],
        "raffle_count": 0
    },
    "processed_posts": [],
    "last_processed_timestamp": 0
}
```

#### **Configuration Parameters**

- **subreddits**: List of subreddit names (without `/r/`) to monitor.
- **max_winners**: Maximum number of winners allowed per raffle.
- **max_reward**: Maximum reward amount in Cannacoin.
- **min_reward**: Minimum reward amount in Cannacoin.
- **min_account_age_days**: Minimum account age in days required to participate.
- **min_comment_karma**: Minimum comment karma required to participate.
- **excluded_bots**: List of bot usernames to exclude from raffles.
- **excluded_users**: List of usernames to exclude from raffles.
- **whitelisted_users**: List of usernames authorized to trigger raffles.
- **raffle_count**: Counter for the number of raffles conducted (used internally).

## Running the Bot

1. **Ensure Environment Variables Are Set**

   Make sure the necessary environment variables are configured as described in the [Installation](#installation) section.

2. **Configure the Bot**

   Update the `bot_config.json` file with your desired settings.

3. **Run the Bot**

   ```bash
   python Cannanoin-Sub-Raffler.py
   ```

   *The bot will start monitoring the specified subreddits for raffle commands.*

## Usage

### **Triggering a Raffle**

Authorized users (moderators or those listed in `whitelisted_users`) can trigger a raffle by commenting a command in the monitored subreddits.

#### **Command Format**

```
!raffle [w number_of_winners] [r reward_amount]
```

- **!raffle**: The command keyword to trigger the bot.
- **w number_of_winners** (optional): Specifies the number of winners.
- **r reward_amount** (optional): Specifies the reward amount in Cannacoin for each winner.

*Parameters can be specified in any order and are optional. If omitted, defaults are used.*

### **Examples of Raffle Commands**

1. **Basic Raffle with Defaults**

   ```
   !raffle
   ```

   *Triggers a raffle with the default number of winners (1) and no reward.*

2. **Specify Number of Winners**

   ```
   !raffle w 3
   ```

   *Triggers a raffle with 3 winners and no reward.*

3. **Specify Reward Amount**

   ```
   !raffle r 5000
   ```

   *Triggers a raffle with the default number of winners (1) and a reward of 5000 Cannacoin for the winner.*

4. **Specify Both Winners and Reward**

   ```
   !raffle w 2 r 2000
   ```

   *Triggers a raffle with 2 winners, each receiving 2000 Cannacoin.*

5. **Alternate Parameter Order**

   ```
   !raffle r 3000 w 4
   ```

   *Triggers a raffle with 4 winners, each receiving 3000 Cannacoin.*

### **Bot's Response**

Upon processing the command, the bot will:

- Validate the command format and parameters.
- Check if the user is authorized to trigger a raffle.
- Select winners randomly from eligible participants.
- Reply to the command with the raffle results, including:
  - Confirmation of the raffle completion.
  - Reward details (if applicable).
  - Participation requirements.
  - List of winners.
  - A thank you message and signature.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

   Click the "Fork" button at the top right of this page.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/yourusername/Cannacoin-Sub-Raffler.git
   ```

3. **Create a Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Changes**

   Implement your feature or bug fix.

5. **Commit Changes**

   ```bash
   git commit -am "Add your commit message here"
   ```

6. **Push to Your Fork**

   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

   Go to the original repository and click "New Pull Request". Select your branch and submit.

## License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute this software.

---

**Disclaimer**: This bot is provided as-is without any guarantees. Use it responsibly and ensure compliance with Reddit's [Terms of Service](https://www.redditinc.com/policies/user-agreement) and [API Guidelines](https://github.com/reddit-archive/reddit/wiki/API).

## Acknowledgments

- **PRAW**: [praw-dev/praw](https://github.com/praw-dev/praw) - The Python Reddit API Wrapper used for interacting with Reddit.
- **Cannacoin Community**: For inspiration and support.

---

Thank you for using the Cannacoin Subreddit Raffle Bot! Enjoy hosting raffles and engaging with your community.

------

Happy Raffle Hosting! 🎉

