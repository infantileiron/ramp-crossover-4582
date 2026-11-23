import os
from pathlib import Path

DATABASE_URL = os.environ['DATABASE_URL']
REDIS_URL = os.environ['REDIS_URL']
JWT_SECRET = os.environ['JWT_SECRET']
EXPORT_DIR = Path(os.environ.get('EXPORT_DIR', '/exports'))
HEARTBEAT = Path('/tmp/ramp-worker.heartbeat')
