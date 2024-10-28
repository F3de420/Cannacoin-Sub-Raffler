# Cannacoin-Sub-Raffler

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![GitHub](https://img.shields.io/badge/License-MIT-brightgreen)

## Overview

**Cannacoin-Sub-Raffler** is a simple yet effective command-line tool that allows users to randomly select winners from comments on a specific Reddit post. This tool is particularly useful for giveaways, contests, and raffles held on Reddit. The script uses the [PRAW](https://praw.readthedocs.io/en/latest/) (Python Reddit API Wrapper) library to interact with Reddit's API.

### Features

- Fetches comments from a specified Reddit post.
- Excludes specific users based on input.
- Randomly selects a specified number of winners.
- Displays eligible commenters and excluded users.
- Color-coded terminal output for better readability.

## Requirements

- Python 3.8 or higher
- [PRAW](https://praw.readthedocs.io/en/latest/) library

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/python-reddit-raffler.git
   cd python-reddit-raffler
   ```

2. **Install the required libraries:**
   ```bash
   pip install praw
   ```

3. **Set up your Reddit application:**
   - Go to [Reddit Apps](https://www.reddit.com/prefs/apps).
   - Create a new application.
   - Take note of your **client_id** and **client_secret**.
   - Make sure to set the redirect URI to `http://www.example.com/unused/redirect/uri`.

## Usage

1. **Open the script:**
   Make sure to replace the `client_id` and `client_secret` in the script with your own credentials:

   ```python
   reddit = praw.Reddit(
       client_id="YOUR_CLIENT_ID",
       client_secret="YOUR_CLIENT_SECRET",
       user_agent="comment_raffle_script",
   )
   ```

2. **Run the script:**
   ```bash
   python reddit_raffler.py
   ```

3. **Input required information:**
   - **Reddit Post ID:** Provide the ID of the Reddit post you want to run the raffle on.
   - **Number of Winners:** Specify how many winners you would like to select.
   - **Excluded Users:** Enter usernames to exclude from the raffle, separated by commas.

4. **Results:**
   The script will display:
   - Users excluded from the raffle.
   - Eligible commenters for the raffle.
   - The randomly selected winners.

## Example Output

```plaintext
--------------------------------------------------

Cannacoin-Sub-Raffler by F3de420 for Stellar CANNACOIN

--------------------------------------------------

Enter the Reddit post ID: <post_id>
How many winners would you like to pick? 3
Enter usernames to exclude, separated by a comma: user1, user2

--------------------------------------------------
Users excluded from the raffle: user1, user2

--------------------------------------------------
Eligible commenters for the raffle:
1. eligible_user1
2. eligible_user2
...

Building suspense... 
...
AND THE WINNER(S) IS:
--------------------------------------------------
🎉 winner1 🎉
🎉 winner2 🎉
🎉 winner3 🎉
🎊 CONGRATULATIONS! 🎊
--------------------------------------------------
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

**Happy Raffle! 🎉**
