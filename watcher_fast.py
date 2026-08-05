from watcher_core import run
from datetime import datetime
import time

while True:

    run()

    now = datetime.now()

    if now.second < 30:
        wait = 30 - now.second
    else:
        wait = 60 - now.second

    time.sleep(wait)