import logging
import sys
import time

from psycopg import OperationalError
from redis import RedisError

from src.db import connect, migrate
from src.queueing import HEARTBEAT_KEY, WAKE_KEY, client
from src.services.candidates import calculate_one

log = logging.getLogger("lexicon.worker")


def run():
    migrate()
    while True:
        try:
            with connect() as db:
                processed = calculate_one(db)
            client.set(HEARTBEAT_KEY, "ready", ex=12)
            if not processed:
                client.blpop(WAKE_KEY, timeout=2)
        except (RedisError, OperationalError):
            log.warning("后台连线暂时中断", exc_info=True)
            time.sleep(2)


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if client.get(HEARTBEAT_KEY) == b"ready" else 1)
    logging.basicConfig(level=logging.INFO)
    run()
