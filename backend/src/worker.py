import logging
import time

from psycopg.types.json import Jsonb
from redis.exceptions import RedisError

from src.config.database import connect, queue
from src.config.settings import HEARTBEAT
from src.services.crossover import analyze
from src.services.export import write_export
from src.services.reports import WAKE_KEY
from src.utils.serial import json_ready

LOGGER = logging.getLogger(__name__)


def process_one():
    with connect() as db:
        job = db.execute("SELECT id, snapshot, fingerprint FROM report WHERE state='queued' "
                         'ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED').fetchone()
        if job is None:
            return False
        try:
            result = json_ready(analyze(job['snapshot']))
            write_export(job['id'], job['snapshot'], job['fingerprint'], result)
        except Exception:
            LOGGER.exception('Report %s failed', job['id'])
            db.execute("UPDATE report SET state='failed', finished_at=now(), error=%s WHERE id=%s",
                       ('计算或导出失败，可使用原参数版本重新运行。', job['id']))
        else:
            db.execute("UPDATE report SET state='ready', finished_at=now(), result=%s WHERE id=%s",
                       (Jsonb(result), job['id']))
        return True


def run():
    while True:
        try:
            processed = process_one()
            HEARTBEAT.touch()
            if not processed:
                try:
                    queue.brpop(WAKE_KEY, timeout=2)
                except RedisError:
                    time.sleep(2)
        except Exception:
            LOGGER.exception('Worker loop will retry')
            time.sleep(2)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run()
