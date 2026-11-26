import logging

from redis import Redis, RedisError

from src.config import settings

WAKE_KEY = "lexicon:scan:notify"
HEARTBEAT_KEY = "lexicon:worker:heartbeat"
client = Redis.from_url(settings.redis_url, socket_connect_timeout=3, socket_timeout=5)
log = logging.getLogger("lexicon.queue")


def wake(scan_id):
    try:
        client.rpush(WAKE_KEY, scan_id)
    except RedisError:
        log.warning("Redis 通知失败。待计算任务仍保存在 PostgreSQL。", exc_info=True)
