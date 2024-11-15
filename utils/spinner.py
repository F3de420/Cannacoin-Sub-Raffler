# utils/spinner.py

import sys
import time
import itertools

def spinner_animation(stop_event):
    """Mostra un'animazione dello spinner nella console."""
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    while not stop_event.is_set():
        sys.stdout.write('\r' + next(spinner) + ' Bot is running...')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\rBot stopped.            \n')
    sys.stdout.flush()
