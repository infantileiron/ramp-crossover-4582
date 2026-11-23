import hashlib
import hmac
import secrets


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return f'{salt}:{digest.hex()}'


def verify_password(password, stored):
    return hmac.compare_digest(hash_password(password, stored.split(':', 1)[0]), stored)
