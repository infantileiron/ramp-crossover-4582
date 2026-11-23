import psycopg
from psycopg.rows import dict_row
from redis import Redis

from src.config.settings import DATABASE_URL, REDIS_URL


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=3)


queue = Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=4)
