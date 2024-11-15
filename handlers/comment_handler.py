# handlers/comment_handler.py

import re
import logging
import random

from config.config import save_config
from utils.pastebin_helper import upload_to_pastebin
from utils.random_org_helper import select_winners_with_random_org
from utils.authentication import connect_to_reddit

logger = logging.getLogger(__name__)

TRIGGER = r'!raffle4canna(?:\s+w\s*(\d+))?(?:\s+r\s*([\d;]+))?'

signature = (
    "\n\n---\n\n"
    "[Cannacoin Raffler](https://github.com/F3de420/Cannacoin-Sub-Raffler) | "
    "[r/StellarCannaCoin](https://www.reddit.com/r/StellarCannaCoin/) | "
    "[r/StellarShroomz](https://www.reddit.com/r/StellarShroomz) | "
    "[StashApp](https://stashapp.cloud/) | "
    "[Cannacoin Discord](https://discord.gg/Xrpxm34QgW) | "
    "[Shroomz Discord](https://discord.gg/PXkKFKwZVA)"
)

def handle_comment(comment, match, data):
    """Handles the comment processing and validation based on trigger pattern."""
    author_name = comment.author.name
    subreddit_name = comment.subreddit.display_name

    # Check if the comment has already been processed
    if comment.id in data["processed_posts"]:
        logger.debug(f"Comment {comment.id} already processed. Skipping.")
        return

    # Extract parameters from the trigger
    num_winners = int(match.group(1)) if match.group(1) else 1
    rewards = [int(r) for r in match.group(2).split(";")] if match.group(2) else [0]

    # Ensure that the number of rewards matches the number of winners
    assigned_rewards = [
        rewards[i] if i < len(rewards) else rewards[-1] for i in range(num_winners)
    ]

    # Calculate the total reward
    total_reward = sum(assigned_rewards) if any(assigned_rewards) else 0

    # Get configurations
    EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
    EXCLUDED_USERS = set(data["config"]["excluded_users"])
    MAX_WINNERS = data["config"]["max_winners"]

    # Validate the number of winners
    if num_winners > MAX_WINNERS:
        logger.warning(f"Number of winners exceeds maximum allowed for raffle by u/{author_name}")
        try:
            comment.reply(
                f"**Error:** Number of winners exceeds the maximum allowed ({MAX_WINNERS})."
            )
        except Exception as e:
            logger.error(f"Failed to post error response: {e}")
        return

    # Get the list of participants
    participants = [
        c.author.name for c in comment.submission.comments.list()
        if c.author and
        c.author.name not in EXCLUDED_BOTS and
        c.author.name not in EXCLUDED_USERS and
        c.author.name != author_name  # Exclude the raffle initiator
    ]

    # Remove duplicates
    participants = list(set(participants))

    # Verify if there are enough participants
    if len(participants) < num_winners:
        logger.warning(f"Not enough participants for raffle by u/{author_name}")
        try:
            comment.reply(
                f"**Error:** Not enough participants to complete the raffle.\n\n"
                f"**Participants Needed:** {num_winners}, but only {len(participants)} were found."
            )
        except Exception as e:
            logger.error(f"Failed to post error response: {e}")
        return

    # Select winners using Random.org
    winners = select_winners_with_random_org(participants, num_winners)
    if not winners:
        # Fallback using the random module
        logger.warning("Random.org not available, using the random module as fallback.")
        winners = random.sample(participants, num_winners)

    # Construct the winners message
    if total_reward == 0:
        # Case when rewards are zero
        results_message = "\n".join([
            f"{i+1}. u/{winner}" for i, winner in enumerate(winners)
        ])
        final_note = ""  # No final note
    else:
        results_message = "\n".join([
            f"{i+1}. u/{winner} - {assigned_rewards[i]} CANNACOIN" for i, winner in enumerate(winners)
        ])
        final_note = (
            "\n\n**Note:** All prizes will be distributed manually. "
            "Winners, please reply to this comment with your Cannacoin wallet address to claim your rewards. "
            "Thank you for participating!"
        )

    logger.info(f"Winners selected: {winners}")

    # Upload participants to Pastebin
    pastebin_link = None
    try:
        participants_formatted = ' | '.join(participants)
        pastebin_link = upload_to_pastebin(
            participants_formatted,
            title=f"Raffle Participants: {comment.submission.id}"
        )
        # Modify the link to point to the raw version
        if 'pastebin.com/' in pastebin_link:
            pastebin_key = pastebin_link.split('/')[-1]
            pastebin_raw_link = f"https://pastebin.com/raw/{pastebin_key}"
        else:
            pastebin_raw_link = pastebin_link
        logger.info(f"Participants uploaded to Pastebin: {pastebin_raw_link}")
    except Exception as e:
        logger.error(f"Failed to upload participants to Pastebin: {e}")
        pastebin_raw_link = "Error uploading participants list to Pastebin."

    # Construct the bot's response
    response = f"**Raffle Completed!**\n\n"
    response += f"**Total Participants:** {len(participants)}\n"
    response += f"[Full List of Eligible Participants]({pastebin_raw_link})\n\n"
    if total_reward > 0:
        response += f"**Total Reward Pool:** {total_reward} CANNACOIN\n\n"
    response += f"**Winners:**\n{results_message}\n\n"
    response += "---\n\n"
    response += "Thank you all for participating!\n\n"
    response += final_note + "\n\n"
    response += signature

    # Reply to the comment
    try:
        comment.reply(response)
        logger.info(f"Posted results successfully in thread: {comment.submission.id}")
    except Exception as e:
        logger.error(f"Failed to post results: {e}")

    # Add the comment to processed posts and save data
    data["processed_posts"].add(comment.id)
    save_config(data)
