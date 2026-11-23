from fastapi import APIRouter, Depends

from src.constants.domain import Role
from src.schemas.inputs import PairCode, PairInput, PlanInput, RouteCode
from src.services import field
from src.services.auth import allow, current_user

router = APIRouter()


@router.get('/routes')
def routes(_=Depends(current_user)):
    return field.routes()


@router.get('/routes/{route_code}/pairs')
def pairs(route_code: RouteCode, _=Depends(current_user)):
    return field.pairs(route_code)


@router.put('/routes/{route_code}/pairs/{code}')
def save_pair(route_code: RouteCode, code: PairCode, data: PairInput, user=Depends(allow(Role.ANALYST))):
    return field.save_pair(route_code, code, data, user['username'])


@router.get('/routes/{route_code}/plans')
def plans(route_code: RouteCode, _=Depends(current_user)):
    return field.plans(route_code)


@router.post('/plans', status_code=201)
def create_plan(data: PlanInput, user=Depends(allow(Role.ANALYST))):
    return field.create_plan(data, user['username'])
