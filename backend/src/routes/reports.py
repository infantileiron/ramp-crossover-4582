from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.constants.domain import Role
from src.controllers.report_files import download
from src.schemas.inputs import ReviewInput, RunInput
from src.services import reports
from src.services.auth import allow, current_user

router = APIRouter(prefix='/reports')
ReportID = Annotated[int, Path(gt=0, le=2147483647)]


@router.get('')
def list_reports(user=Depends(current_user)):
    return reports.list_reports(user)


@router.post('', status_code=202)
def create_run(data: RunInput, user=Depends(allow(Role.ANALYST))):
    return reports.create_run(data.plan_id, user['username'])


@router.get('/{report_id}')
def detail(report_id: ReportID, user=Depends(current_user)):
    return reports.get_report(report_id, user)


@router.get('/{report_id}/export')
def export(report_id: ReportID, user=Depends(current_user)):
    return download(report_id, user)


@router.post('/{report_id}/publish')
def review(report_id: ReportID, data: ReviewInput, user=Depends(allow(Role.REVIEWER))):
    return reports.publish(report_id, data, user)
