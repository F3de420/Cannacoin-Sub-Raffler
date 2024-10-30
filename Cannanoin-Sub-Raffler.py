import praw
import random
import time

# Utility function for color coding
def colored(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

# Color codes
COLORS = {
    "header": "1;34",   # Blue
    "info": "1;36",     # Cyan
    "warning": "1;33",  # Yellow
    "error": "1;31",    # Red
    "success": "1;32",  # Green
}

# Header
print("\n" + "-" * 50)
print("\n" + colored("Python Reddit Raffler", COLORS["header"]) + " by F3de420 for " + colored("Stellar CANNACOIN", COLORS["success"]))
print("\n" + "-" * 50)

# Reddit authentication using app credentials
reddit = praw.Reddit(
    client_id="Hi_UFHf7hZ5PUwSB0qfRNg",
    client_secret="tOgKu9cbY1TjMEzJbgn0mFyirZpnjw",
    user_agent="comment_raffle_script",
)

# Prompt for the Reddit post ID and other inputs
post_id = input(colored("Enter the Reddit post ID: ", COLORS["header"]))
num_winners = int(input(colored("How many winners would you like to pick? ", COLORS["header"])))
exclude_users_input = input(colored("Enter usernames to exclude, separated by a comma: ", COLORS["error"])).split(",")

# Process exclusion list
exclude_users = {user.strip().lower() for user in exclude_users_input if user.strip()}

# Initialize sets for eligible and excluded users
eligible_authors = set()
excluded_authors = set()

# Fetch comments from the submission
submission = reddit.submission(id=post_id)
submission.comments.replace_more(limit=None)

# Process each comment
for comment in submission.comments.list():
    author_name = comment.author.name.lower()  # Normalize to lowercase

    # Skip if author is in the exclusion list
    if author_name in exclude_users:
        excluded_authors.add(author_name)
    else:
        eligible_authors.add(author_name)  # Otherwise, add to eligible list

# Remove any overlap between excluded and eligible authors
eligible_authors -= excluded_authors

# Check if there are eligible commenters left
if not eligible_authors:
    print(colored("No commenters are eligible after filtering and exclusions. Exiting the program.", COLORS["error"]))
    exit()

# Display excluded users and eligible users
if excluded_authors:
    print("\n" + "-" * 50)
    print(colored("Users excluded from the raffle:", COLORS["error"]))
    print(", ".join(excluded_authors))

print("\n" + "-" * 50)
print("Eligible commenters for the raffle:")
for i, author in enumerate(eligible_authors, start=1):
    print(colored(f"{i}. {author}", COLORS["success"]))
    time.sleep(0.25)  # Interval of 0.25 seconds between each name

# Display suspense loader
print("\n" + colored("Building suspense...", COLORS["warning"]), end="")
# print("")
for _ in range(5):
    print(colored(".", COLORS["warning"]), end="", flush=True)
    time.sleep(0.4)

# Randomly select winners from eligible authors
eligible_authors = list(eligible_authors)  # Convert to list for random sampling
if num_winners > len(eligible_authors):
    print(colored(f"\n\nWarning: Not enough commenters to select {num_winners} winners.", COLORS["error"]))
    winners = random.sample(eligible_authors, len(eligible_authors))
else:
    winners = random.sample(eligible_authors, k=num_winners)

# Display winners
print("")
print("\n" + colored("AND THE WINNER(S) IS...", COLORS["header"]), end="")
for _ in range(5):
    print(colored(".", COLORS["header"]), end="", flush=True)
    time.sleep(0.4)
print("")
print("-" * 50)
time.sleep(0.5)
print("")
for winner in winners:
    print(colored(f"🎉 {winner} 🎉", COLORS["success"]))

print("")
print("\n" + colored("🎊 CONGRATULATIONS! 🎊", COLORS["warning"]))
print("")
print("-" * 50)
