import sys
import time
from urllib.request import urlopen

from src.config.settings import HEARTBEAT


def check(kind):
    if kind == 'worker':
        return time.time() - HEARTBEAT.stat().st_mtime < 12
    with urlopen('http://127.0.0.1:8000/health', timeout=2) as response:
        return response.status == 200


if __name__ == '__main__':
    try:
        sys.exit(0 if check(sys.argv[1]) else 1)
    except OSError:
        sys.exit(1)
