import hashlib
import json
from decimal import Decimal


def json_ready(value):
    return json.loads(json.dumps(value, default=lambda item: float(item) if isinstance(item, Decimal) else item.isoformat()))


def fingerprint(snapshot):
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()
