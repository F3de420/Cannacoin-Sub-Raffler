# utils/random_org_helper.py

import os
import logging
import random
import requests

logger = logging.getLogger(__name__)

RANDOM_ORG_API_KEY = os.getenv("RANDOM_ORG_API_KEY")

def select_winners_with_random_org(participants, num_winners):
    """Seleziona i vincitori utilizzando l'API di Random.org."""
    try:
        api_url = 'https://api.random.org/json-rpc/4/invoke'
        headers = {'Content-Type': 'application/json'}
        data = {
            'jsonrpc': '2.0',
            'method': 'generateIntegers',
            'params': {
                'apiKey': RANDOM_ORG_API_KEY,
                'n': num_winners,
                'min': 0,
                'max': len(participants) - 1,
                'replacement': False
            },
            'id': random.randint(1, 100000)
        }
        response = requests.post(api_url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        random_data = response.json()

        if 'error' in random_data:
            logger.error(f"Errore da Random.org: {random_data['error']}")
            return None

        indices = random_data['result']['random']['data']
        winners = [participants[i] for i in indices]
        return winners
    except Exception as e:
        logger.error(f"Impossibile ottenere numeri casuali da Random.org: {e}")
        return None
