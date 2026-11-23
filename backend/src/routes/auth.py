from fastapi import APIRouter, Depends

from src.schemas.inputs import Credentials
from src.services.auth import current_user, login

router = APIRouter()


@router.post('/login')
def authenticate(credentials: Credentials):
    return login(credentials.username, credentials.password)


@router.get('/me')
def me(user=Depends(current_user)):
    return user
