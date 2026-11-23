from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config.database import connect
from src.config.settings import JWT_SECRET
from src.utils.passwords import verify_password

bearer = HTTPBearer(auto_error=False)
DUMMY_HASH = f"{'0' * 32}:{'0' * 128}"


def login(username, password):
    with connect() as db:
        user = db.execute('SELECT * FROM app_user WHERE username=%s', (username,)).fetchone()
    if not verify_password(password, user['password_hash'] if user else DUMMY_HASH) or not user:
        raise HTTPException(401, '账号或密码有误')
    user.pop('password_hash')
    now = datetime.now(timezone.utc)
    token = jwt.encode({'sub': user['username'], 'iat': now, 'exp': now + timedelta(hours=8)}, JWT_SECRET, algorithm='HS256')
    return {'token': token, 'user': user}


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, '请先登录')
    try:
        claims = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=['HS256'], options={'require': ['exp', 'sub']})
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, '登录已失效，请重新登录') from exc
    with connect() as db:
        user = db.execute('SELECT username, display_name, role FROM app_user WHERE username=%s', (claims['sub'],)).fetchone()
    if not user:
        raise HTTPException(401, '登录已失效，请重新登录')
    return user


def allow(*roles):
    def authorized(user=Depends(current_user)):
        if user['role'] not in roles:
            raise HTTPException(403, '当前账号没有此操作权限')
        return user
    return authorized
