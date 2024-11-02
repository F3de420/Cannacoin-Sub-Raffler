import os
import re
import json
import time
import requests
from bot import login, is_moderator

# Configurazione file e trigger
CONFIG_FILE = "bot_data.json"
TRIGGER = r'!canna-raffler\s*(\d*)'
RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")  # La chiave API di Random.org

# Carica dati persistenti
def load_data():
    """Carica i dati persistenti da file JSON."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"config": {"subreddits": ["NomeSubredditPrincipale"], "max_winners": 5, 
                       "excluded_bots": ["AutoModerator", "timee_bot"], "excluded_users": [], "raffle_count": 0},
            "processed_posts": [], "last_processed_timestamp": 0}

# Salva i dati persistenti
def save_data(data):
    """Salva i dati persistenti su file JSON."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Inizializza i dati caricati
data = load_data()
PROCESSED_POSTS = set(data["processed_posts"])
SUBREDDITS = data["config"]["subreddits"]
EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
EXCLUDED_USERS = set(data["config"]["excluded_users"])
MAX_WINNERS = data["config"]["max_winners"]

# Inizializza Reddit
reddit = login()

def monitor_subreddits():
    """Monitora i subreddit e gestisce i raffle quando viene rilevato il trigger."""
    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        for comment in subreddit.stream.comments(skip_existing=True):
            if comment.created_utc <= data["last_processed_timestamp"]:
                continue
            
            if match := re.search(TRIGGER, comment.body):
                num_winners = int(match.group(1)) if match.group(1) else 1
                num_winners = min(num_winners, MAX_WINNERS)
                handle_raffle(comment, num_winners, subreddit_name)
                
            data["last_processed_timestamp"] = max(data["last_processed_timestamp"], comment.created_utc)
            save_data(data)

def get_random_numbers(n, min_val, max_val):
    """Ottieni `n` numeri casuali unici da Random.org tra min_val e max_val."""
    url = "https://api.random.org/json-rpc/2/invoke"
    headers = {"content-type": "application/json"}
    params = {
        "jsonrpc": "2.0",
        "method": "generateIntegers",
        "params": {
            "apiKey": RANDOM_ORG_API_KEY,
            "n": n,
            "min": min_val,
            "max": max_val,
            "replacement": False
        },
        "id": 42
    }
    response = requests.post(url, json=params, headers=headers)
    if response.status_code == 200:
        result = response.json().get("result", {}).get("random", {}).get("data", [])
        return result
    else:
        raise Exception("Errore nella richiesta a Random.org")

def handle_raffle(trigger_comment, num_winners, subreddit_name):
    """Gestisce il processo di raffle."""
    author_name = trigger_comment.author.name
    post_id = trigger_comment.submission.id

    if post_id in PROCESSED_POSTS:
        print(f"Il bot ha giÃ  processato il post {post_id}. Operazione ignorata.")
        return

    if not is_moderator(reddit, author_name, subreddit_name):
        trigger_comment.reply("Questo bot Ã¨ attualmente riservato ai moderatori del subreddit.")
        print(f"Utente {author_name} ha tentato di usare il bot senza permessi.")
        return

    PROCESSED_POSTS.add(post_id)
    data["processed_posts"] = list(PROCESSED_POSTS)
    save_data(data)

    post = trigger_comment.submission
    post.comments.replace_more(limit=None)
    all_comments = post.comments.list()

    participants = set()
    for comment in all_comments:
        if comment.author and comment.author.name not in EXCLUDED_BOTS \
                and comment.author.name != author_name \
                and comment.author.name not in EXCLUDED_USERS:
            participants.add(comment.author.name)

    participants_list = list(participants)
    if len(participants_list) < num_winners:
        trigger_comment.reply(f"Non ci sono abbastanza partecipanti per selezionare {num_winners} vincitori.")
        return

    # Usa Random.org per estrarre gli indici casuali dei vincitori
    try:
        winner_indices = get_random_numbers(num_winners, 0, len(participants_list) - 1)
        winners = [participants_list[i] for i in winner_indices]
    except Exception as e:
        print("Errore nell'estrazione con Random.org:", e)
        trigger_comment.reply("C'Ã¨ stato un errore nell'estrazione dei vincitori.")
        return

    winners_text = '\n'.join(f"- {winner}" for winner in winners)
    data["config"]["raffle_count"] += 1
    save_data(data)

    response_text = f"ðŸŽ‰ **Raffle completato!**\n\nEcco i vincitori:\n\n{winners_text}\n\nGrazie a tutti per la partecipazione!"
    trigger_comment.reply(response_text)
    print(f"Raffle completato nel thread {post.id}. Vincitori: {winners}")

if __name__ == "__main__":
    print("Inizio monitoraggio subreddit...")
    monitor_subreddits()
