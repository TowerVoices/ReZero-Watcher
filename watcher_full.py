from watcher_core import run_full
from datetime import datetime
import time

last_full_minute = -1

while True:

    now = datetime.now()

    if (
        now.minute % 5 == 0
        and now.second < 30
        and now.minute != last_full_minute
    ):

        run_full()

        last_full_minute = now.minute

    time.sleep(1)