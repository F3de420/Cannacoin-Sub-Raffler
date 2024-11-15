# handlers/comment_handler.py

import re
import logging
import random

from config.config import save_config
from utils.pastebin_helper import upload_to_pastebin
from utils.random_org_helper import select_winners_with_random_org

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

def handle_comment(comment, match, data, reddit_instance):
    """Gestisce l'elaborazione del commento e la validazione in base al pattern del trigger."""
    author_name = comment.author.name
    subreddit_name = comment.subreddit.display_name

    # Controlla se il commento è già stato elaborato
    if comment.id in data["processed_posts"]:
        logger.debug(f"Commento {comment.id} già elaborato. Salto.")
        return

    # Estrae i parametri dal trigger
    num_winners = int(match.group(1)) if match.group(1) else 1
    rewards = [int(r) for r in match.group(2).split(";")] if match.group(2) else [0]

    # Assicura che il numero di premi corrisponda al numero di vincitori
    assigned_rewards = [
        rewards[i] if i < len(rewards) else rewards[-1] for i in range(num_winners)
    ]

    # Calcola il premio totale
    total_reward = sum(assigned_rewards) if any(assigned_rewards) else 0

    # Ottiene le configurazioni
    EXCLUDED_BOTS = set(data["config"]["excluded_bots"])
    EXCLUDED_USERS = set(data["config"]["excluded_users"])
    MAX_WINNERS = data["config"]["max_winners"]

    # Valida il numero di vincitori
    if num_winners > MAX_WINNERS:
        logger.warning(f"Numero di vincitori supera il massimo consentito per il raffle di u/{author_name}")
        try:
            comment.reply(
                f"**Errore:** Il numero di vincitori supera il massimo consentito ({MAX_WINNERS})."
            )
        except Exception as e:
            logger.error(f"Impossibile pubblicare la risposta di errore: {e}")
        return

    # Ottiene la lista dei partecipanti
    participants = [
        c.author.name for c in comment.submission.comments.list()
        if c.author and
        c.author.name not in EXCLUDED_BOTS and
        c.author.name not in EXCLUDED_USERS and
        c.author.name != author_name  # Esclude chi ha iniziato il raffle
    ]

    # Rimuove i duplicati
    participants = list(set(participants))

    # Verifica se ci sono abbastanza partecipanti
    if len(participants) < num_winners:
        logger.warning(f"Non ci sono abbastanza partecipanti per il raffle di u/{author_name}")
        try:
            comment.reply(
                f"**Errore:** Non ci sono abbastanza partecipanti per completare il raffle.\n\n"
                f"**Partecipanti necessari:** {num_winners}, ma ne sono stati trovati solo {len(participants)}."
            )
        except Exception as e:
            logger.error(f"Impossibile pubblicare la risposta di errore: {e}")
        return

    # Seleziona i vincitori utilizzando Random.org
    winners = select_winners_with_random_org(participants, num_winners)
    if not winners:
        # Fallback utilizzando il modulo random
        logger.warning("Random.org non disponibile, utilizzo il modulo random come fallback.")
        winners = random.sample(participants, num_winners)

    # Costruisce il messaggio dei vincitori
    if total_reward == 0:
        # Caso in cui i premi sono zero
        results_message = "\n".join([
            f"{i+1}. u/{winner}" for i, winner in enumerate(winners)
        ])
        final_note = ""  # Nessuna nota finale
    else:
        results_message = "\n".join([
            f"{i+1}. u/{winner} - {assigned_rewards[i]} CANNACOIN" for i, winner in enumerate(winners)
        ])
        final_note = (
            "\n\n**Nota:** Tutti i premi saranno distribuiti manualmente. "
            "Vincitori, per favore rispondete a questo commento con il vostro indirizzo wallet Cannacoin per ricevere i premi. "
            "Grazie per aver partecipato!"
        )

    logger.info(f"Vincitori selezionati: {winners}")

    # Carica i partecipanti su Pastebin
    pastebin_link = None
    try:
        participants_formatted = ' | '.join(participants)
        pastebin_link = upload_to_pastebin(
            participants_formatted,
            title=f"Raffle Participants: {comment.submission.id}"
        )
        # Modifica il link per puntare alla versione raw
        if 'pastebin.com/' in pastebin_link:
            pastebin_key = pastebin_link.split('/')[-1]
            pastebin_raw_link = f"https://pastebin.com/raw/{pastebin_key}"
        else:
            pastebin_raw_link = pastebin_link
        logger.info(f"Partecipanti caricati su Pastebin: {pastebin_raw_link}")
    except Exception as e:
        logger.error(f"Impossibile caricare i partecipanti su Pastebin: {e}")
        pastebin_raw_link = "Errore nel caricare la lista dei partecipanti su Pastebin."

    # Costruisce la risposta del bot
    response = f"**Raffle Completato!**\n\n"
    response += f"**Total Participants:** {len(participants)}\n"
    response += f"[Full List of Eligible Participants]({pastebin_raw_link})\n\n"
    if total_reward > 0:
        response += f"**Total Reward Pool:** {total_reward} CANNACOIN\n\n"
    response += f"**Winners:**\n{results_message}\n\n"
    response += "---\n\n"
    response += "Thank you all for participating!\n\n"
    response += final_note + "\n\n"
    response += signature

    # Risponde al commento
    try:
        comment.reply(response)
        logger.info(f"Risultati pubblicati con successo nel thread: {comment.submission.id}")
    except Exception as e:
        logger.error(f"Impossibile pubblicare i risultati: {e}")

    # Aggiunge il commento ai post elaborati e salva i dati
    data["processed_posts"].add(comment.id)
    save_config(data)
