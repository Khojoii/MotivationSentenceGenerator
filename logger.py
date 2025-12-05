import os
import logging
from datetime import datetime

if not os.path.exists("logs"):
    os.makedirs("logs")


now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"logs/{now}.log"

# logger config
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

def get_logger():
    return logging.getLogger()