# Python standard libraries
import os
import time

DELAY_SECONDS = 60
def check_delay(last_time):
    now = time.time()
    elapsed = now - last_time
    if elapsed < DELAY_SECONDS:
        return False, DELAY_SECONDS - int(elapsed)
    return True, now
