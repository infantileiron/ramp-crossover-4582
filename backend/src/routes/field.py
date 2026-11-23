from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.constants.domain import Role
from src.schemas.inputs import (
    PairCode, PairInput, PlanInput, RouteCode, SessionCreate, SessionStart, SessionSwap, SessionTimes,
)
from src.services import field, sessions
from src.services.auth import allow, current_user

router = APIRouter()
SessionID = Annotated[int, Path(gt=0, le=2147483647)]
SeatPath = Annotated[int, Path(ge=1, le=2)]


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


@router.get('/routes/{route_code}/sessions')
def list_sessions(route_code: RouteCode, _=Depends(current_user)):
    return sessions.sessions(route_code)


@router.post('/routes/{route_code}/sessions', status_code=201)
def create_session(route_code: RouteCode, data: SessionCreate, user=Depends(allow(Role.ANALYST))):
    return sessions.create_session(route_code, data, user['username'])


@router.post('/sessions/{session_id}/swap/{seat}', status_code=201)
def swap_member(session_id: SessionID, seat: SeatPath, data: SessionSwap, user=Depends(allow(Role.ANALYST))):
    return sessions.swap_member(session_id, seat, data, user['username'])


@router.post('/sessions/{session_id}/start', status_code=201)
def start_session(session_id: SessionID, data: SessionStart, user=Depends(allow(Role.ANALYST))):
    return sessions.start_session(session_id, data, user['username'])


@router.put('/sessions/{session_id}/times/{seat}')
def record_times(session_id: SessionID, seat: SeatPath, data: SessionTimes, user=Depends(allow(Role.ANALYST))):
    return sessions.record_times(session_id, seat, data, user['username'])
