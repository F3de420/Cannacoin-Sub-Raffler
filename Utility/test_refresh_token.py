import os
import praw

# Carica le variabili d'ambiente
CLIENT_ID = "APP_ID"
CLIENT_SECRET = "APP_SECRET"
REFRESH_TOKEN = "APP_REFRESH"
USER_AGENT = "canna_raffler_bot test refreh token"

# Configura l'istanza di Reddit
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    refresh_token=REFRESH_TOKEN,
    user_agent=USER_AGENT
)

# Test: recupera il nome utente per verificare che il refresh token funzioni
try:
    user = reddit.user.me()
    print(f"Autenticazione riuscita! Nome utente: {user.name}")
except Exception as e:
    print("Errore nell'autenticazione:", e)
